import os
import json
import hashlib
import urllib.request
import pg8000.dbapi
import boto3
from base64 import b64decode

SOURCE_NAME = os.environ["SOURCE_NAME"]
RSS_URL = os.environ["RSS_URL"]

# Decrypt the password once in the global scope (init phase) to keep handler execution times fast.
# This prevents the KMS decryption latency from consuming the handler's runtime on warm starts.
ENCRYPTED_DB_PASSWORD = os.environ['DB_PASSWORD']
DECRYPTED_DB_PASSWORD = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_DB_PASSWORD),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')


def lambda_handler(event, context):
    try:
        # 1. Download raw RSS data
        print(f"Downloading RSS data from {RSS_URL}...", flush=True)
        with urllib.request.urlopen(RSS_URL, timeout=10) as response:
            raw_data = response.read()  # bytes

        # 2. Calculate MD5 hash for deduplication
        hex_hash = hashlib.md5(raw_data).hexdigest()

        # 3. Convert RSS body to text
        body_text = raw_data.decode("utf-8", errors="replace")

        # 4. Insert into RDS
        print("Connecting to RDS and executing query...", flush=True)
        inserted = insert_into_rds(
            db_password=DECRYPTED_DB_PASSWORD,
            source=SOURCE_NAME,
            content_hash=hex_hash,
            body=body_text,
        )
        print(f"RDS operation complete. Inserted new row: {inserted}", flush=True)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Andmed edukalt töödeldud",
                    "hash": hex_hash,
                    "inserted": inserted,
                    "data_size_bytes": len(raw_data),
                    "data_preview": body_text[:200],
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        print(f"Execution failed: {str(e)}", flush=True)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Viga voo töötlemisel",
                    "error": str(e),
                },
                ensure_ascii=False,
            ),
        }


def insert_into_rds(db_password, source, content_hash, body):
    conn = None
    cur = None
    try:
        conn = pg8000.dbapi.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", 5432)),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=db_password,
            timeout=5,
        )

        insert_sql = """
            INSERT INTO bronze.raw(source, hash, body)
            VALUES (%s, %s, %s)
            ON CONFLICT (hash) DO NOTHING;
        """

        cur = conn.cursor()
        cur.execute(insert_sql, (source, content_hash, body))
        inserted = cur.rowcount == 1

        conn.commit()
        return inserted

    except Exception as db_err:
        print(f"Database error occurred: {str(db_err)}", flush=True)
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass