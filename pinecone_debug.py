# pinecone_debug.py

import os
import traceback
from dotenv import load_dotenv
from pinecone import Pinecone

def main():
    load_dotenv()

    api_key = os.getenv("PINECONE_API_KEY")
    env_var = os.getenv("PINECONE_ENVIRONMENT")
    index_name = os.getenv("PINECONE_INDEX_NAME")

    print("DEBUG ▶ PINECONE_API_KEY:", repr(api_key))
    print("DEBUG ▶ PINECONE_ENVIRONMENT:", repr(env_var))
    print("DEBUG ▶ PINECONE_INDEX_NAME:", repr(index_name))
    print()

    # 1) Verify neither is None or empty
    if not api_key:
        print("ERROR ▶ PINECONE_API_KEY is not set or empty.")
        return
    if not env_var:
        print("ERROR ▶ PINECONE_ENVIRONMENT is not set or empty.")
        return
    if not index_name:
        print("ERROR ▶ PINECONE_INDEX_NAME is not set or empty.")
        return

    # 2) Attempt to create the Pinecone client
    try:
        print("DEBUG ▶ Attempting to instantiate Pinecone client …")
        pc = Pinecone(api_key=api_key, environment=env_var)
        print("DEBUG ▶ Pinecone client created successfully.")
    except Exception as e:
        print("ERROR ▶ Could not create Pinecone client:")
        traceback.print_exc()
        return

    # 3) Attempt to list indexes
    try:
        print("DEBUG ▶ Calling pc.list_indexes() …")
        indexes = pc.list_indexes()
        print("DEBUG ▶ list_indexes() returned:", indexes)
    except Exception as e:
        print("ERROR ▶ pc.list_indexes() raised an exception:")
        traceback.print_exc()

if __name__ == "__main__":
    main()