"""
Database Diagnostic Tool

Quick script to check what applications are in the database
and why the background processor might not be finding them.
"""

import asyncio
import os
from dotenv import load_dotenv
from tools.database_tool import DatabaseTool

load_dotenv()


async def diagnose():
    """Diagnose database state."""
    database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
    db_tool = DatabaseTool(database_url)
    
    try:
        await db_tool.connect()
        print("\n" + "=" * 60)
        print("DATABASE DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Get statistics
        stats = await db_tool.get_application_statistics()
        print("\n📊 STATISTICS:")
        print(f"  Status counts: {stats.get('status_counts', {})}")
        print(f"  Screening completed: {stats.get('screening_completed', 0)}")
        print(f"  Screening pending: {stats.get('screening_pending', 0)}")
        print(f"  Average risk score: {stats.get('average_risk_score', 0):.2f}")
        
        # Get all applications
        apps = await db_tool.get_all_applications_debug()
        print(f"\n📋 ALL APPLICATIONS ({len(apps)} total):")
        print(f"{'ID':<38} {'Name':<25} {'Status':<15} {'Completed':<10} {'Created'}")
        print("-" * 120)
        for app in apps:
            app_id = app['application_id']
            name = f"{app['first_name']} {app['last_name']}"
            status = app['status']
            completed = str(app['screening_completed'])
            created = str(app['created_at'])
            print(f"{app_id:<38} {name:<25} {status:<15} {completed:<10} {created}")
        
        # Get pending applications using the actual query
        pending = await db_tool.get_pending_applications(limit=100)
        print(f"\n🔍 PENDING APPLICATIONS QUERY RESULT ({len(pending)} found):")
        if pending:
            print(f"{'ID':<38} {'Name':<25} {'Status':<15} {'Completed':<10} {'Created'}")
            print("-" * 120)
            for app in pending:
                app_id = app['application_id']
                name = f"{app['first_name']} {app['last_name']}"
                status = app['status']
                completed = str(app['screening_completed'])
                created = str(app['created_at'])
                print(f"{app_id:<38} {name:<25} {status:<15} {completed:<10} {created}")
        else:
            print("  ⚠️  NO APPLICATIONS FOUND")
            print("  This means no applications have status='PENDING' AND screening_completed=0")
            print("\n  Possible issues:")
            print("    1. Status value is not exactly 'PENDING' (check for case/whitespace)")
            print("    2. screening_completed is not 0 (might be NULL or 1)")
            print("    3. No applications exist in the database")
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS COMPLETE")
        print("=" * 60 + "\n")
        
    finally:
        await db_tool.disconnect()


if __name__ == "__main__":
    asyncio.run(diagnose())
