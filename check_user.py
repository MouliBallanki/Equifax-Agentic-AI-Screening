"""
Check user account and applications.
"""

import asyncio
import os
from dotenv import load_dotenv
from tools.database_tool import DatabaseTool

load_dotenv()


async def main():
    email = "mouli.ballanki1211313131@loqbox.com"
    
    database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
    db = DatabaseTool(database_url)
    
    try:
        await db.connect()
        print(f"✅ Connected to database\n")
        
        # Check if user exists
        async with db.pool.acquire() as conn:
            import aiomysql
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT user_id, email, first_name, last_name, created_at FROM users WHERE email = %s",
                    (email,)
                )
                user = await cursor.fetchone()
                
                if not user:
                    print(f"❌ User not found: {email}")
                    print(f"💡 The user needs to sign up first")
                    return
                
                print(f"👤 User found:")
                print(f"   User ID: {user['user_id']}")
                print(f"   Name: {user['first_name']} {user['last_name']}")
                print(f"   Email: {user['email']}")
                print(f"   Created: {user['created_at']}\n")
                
                # Check applications
                await cursor.execute(
                    """
                    SELECT application_id, first_name, last_name, email, status,
                           screening_completed, risk_score, created_at, screened_at
                    FROM applications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user['user_id'],)
                )
                applications = await cursor.fetchall()
                
                if not applications:
                    print(f"📋 No applications found for this user")
                    print(f"💡 User can submit an application at /apply")
                else:
                    print(f"📋 Found {len(applications)} application(s):\n")
                    for app in applications:
                        print(f"   Application ID: {app['application_id']}")
                        print(f"   Name: {app['first_name']} {app['last_name']}")
                        print(f"   Email: {app['email']}")
                        print(f"   Status: {app['status']}")
                        print(f"   Screening Completed: {app['screening_completed']}")
                        print(f"   Risk Score: {app['risk_score']}")
                        print(f"   Created: {app['created_at']}")
                        print(f"   Screened: {app['screened_at']}")
                        print()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
