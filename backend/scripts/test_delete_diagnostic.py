#!/usr/bin/env python3
"""
Diagnostic script to test document deletion.
Run with: python backend/scripts/test_delete_diagnostic.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.database import SessionLocal
from database.models.documents import delete_document, get_all_documents, get_document


def main():
    print("\n" + "=" * 80)
    print("DOCUMENT DELETION DIAGNOSTIC")
    print("=" * 80)

    session = SessionLocal()

    try:
        # List all users
        print("\n[USERS] Checking for users in database:")
        from sqlalchemy import select

        from database.models.user import User

        all_users = session.execute(select(User)).scalars().all()
        print(f"  Found {len(all_users)} users")
        for user in all_users:
            docs = get_all_documents(session, user.user_id)
            print(f"    - User {user.user_id} ({user.email}): {len(docs)} documents")

        # Get a specific user to test with
        test_user = None
        if all_users:
            test_user = all_users[0]

        if not test_user:
            print("\n[ERROR] No users found in database - cannot test deletion")
            return

        print(f"\n[TEST] Using test user: {test_user.user_id} ({test_user.email})")

        # List documents for this user
        docs = get_all_documents(session, test_user.user_id)
        print(f"\n[DOCUMENTS] User has {len(docs)} documents:")
        for doc in docs:
            print(
                f"  - doc_id={doc.doc_id}, type={doc.document_type}, name={doc.document_name}"
            )

        if not docs:
            print("\n[ERROR] User has no documents - cannot test deletion")
            return

        # Pick first document to test delete on
        test_doc = docs[0]
        print(f"\n[DELETE-TEST] Testing deletion of doc_id={test_doc.doc_id}")
        print(f"  Document name: {test_doc.document_name}")
        print(f"  Document type: {test_doc.document_type}")
        print(f"  Owner user_id: {test_doc.user_id}")

        # Test get_document
        print(f"\n[GET-TEST] Testing get_document({test_doc.doc_id}):")
        retrieved = get_document(session, test_doc.doc_id)
        if retrieved:
            print(f"  ✓ Successfully retrieved: doc_id={retrieved.doc_id}")
        else:
            print("  ❌ Failed to retrieve document")
            return

        # Test delete_document
        print(f"\n[DELETE-EXEC] Executing delete_document({test_doc.doc_id}):")
        result = delete_document(session, test_doc.doc_id)
        print(f"  Result: {result}")

        if result:
            print("  ✓ Delete completed successfully")

            # Verify deletion
            print("\n[VERIFY] Verifying deletion:")
            retrieved_after = get_document(session, test_doc.doc_id)
            if retrieved_after is None:
                print("  ✓ Document confirmed deleted from database")
            else:
                print("  ❌ Document still exists after delete!")
                print(
                    f"     doc_id={retrieved_after.doc_id}, name={retrieved_after.document_name}"
                )
        else:
            print("  ❌ Delete failed")

            # Check if document still exists
            retrieved_after = get_document(session, test_doc.doc_id)
            if retrieved_after:
                print(f"  Document still exists: doc_id={retrieved_after.doc_id}")

    finally:
        session.close()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
