"""
Database Initialization Script

Generates 10 sample applicants:
- 2 approved (screening_completed=1)
- 2 rejected (screening_completed=1)
- 6 pending (screening_completed=0)
"""

import pymysql
import json
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker()

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL user
    'password': 'sails@123',  # Change this to your MySQL password
    'database': 'equifax_screening',
    'charset': 'utf8mb4'
}

# Employment statuses
EMPLOYMENT_STATUSES = ['full-time', 'part-time', 'self-employed', 'contract']

# US States
US_STATES = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']


def generate_ssn():
    """Generate fake SSN."""
    return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def generate_applicant_data(status='pending', screening_completed=0):
    """Generate a single applicant record."""
    
    application_id = str(uuid.uuid4())
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.free_email_domain()}"
    phone = fake.phone_number()[:20]
    ssn = generate_ssn()
    date_of_birth = fake.date_of_birth(minimum_age=21, maximum_age=70)
    
    # Address
    street = fake.street_address()
    city = fake.city()
    state = random.choice(US_STATES)
    zip_code = fake.zipcode()
    
    # Employment
    employer_name = fake.company()
    job_title = fake.job()
    employment_status = random.choice(EMPLOYMENT_STATUSES)
    annual_income = round(random.uniform(25000, 150000), 2)
    years_employed = round(random.uniform(0.5, 20), 1)
    employer_phone = fake.phone_number()[:20]
    
    # Rental History
    current_landlord = fake.name() if random.random() > 0.2 else None
    current_landlord_phone = fake.phone_number()[:20] if current_landlord else None
    monthly_rent = round(random.uniform(800, 3500), 2)
    years_at_current = round(random.uniform(0.5, 10), 1)
    reason_for_leaving = random.choice([
        'Moving for work',
        'Seeking larger space',
        'Closer to family',
        'Better neighborhood',
        None
    ])
    
    # Additional Info
    pets = random.choice([True, False])
    smoker = random.choice([True, False])
    bankruptcy_history = random.choice([True, False]) if random.random() < 0.1 else False
    eviction_history = random.choice([True, False]) if random.random() < 0.05 else False
    
    # Create application_data JSON
    application_data = {
        "applicant": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "ssn": ssn,
            "date_of_birth": str(date_of_birth),
            "current_address": {
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_code
            }
        },
        "employment": {
            "employer_name": employer_name,
            "job_title": job_title,
            "employment_status": employment_status,
            "annual_income": annual_income,
            "years_employed": years_employed,
            "employer_phone": employer_phone
        },
        "rental_history": {
            "current_landlord": current_landlord,
            "current_landlord_phone": current_landlord_phone,
            "monthly_rent": monthly_rent,
            "years_at_current": years_at_current,
            "reason_for_leaving": reason_for_leaving
        },
        "additional_info": {
            "pets": pets,
            "smoker": smoker,
            "bankruptcy_history": bankruptcy_history,
            "eviction_history": eviction_history
        }
    }
    
    # Final decision and risk score for completed screenings
    final_decision = None
    decision_reason = None
    risk_score = None
    screened_at = None
    
    if screening_completed == 1:
        if status == 'approved':
            risk_score = round(random.uniform(65, 95), 2)
            final_decision = {
                "decision": "approved",
                "recommendation": "approve",
                "confidence": round(random.uniform(0.8, 0.95), 2)
            }
            decision_reason = "Applicant meets all criteria with good credit history and stable employment"
        else:  # rejected
            risk_score = round(random.uniform(20, 50), 2)
            final_decision = {
                "decision": "rejected",
                "recommendation": "reject",
                "confidence": round(random.uniform(0.75, 0.9), 2)
            }
            decision_reason = random.choice([
                "Insufficient income to rent ratio",
                "Credit score below minimum threshold",
                "Prior eviction history",
                "Unable to verify employment",
                "Negative rental history"
            ])
        screened_at = datetime.now() - timedelta(days=random.randint(1, 30))
    
    created_at = datetime.now() - timedelta(days=random.randint(1, 90))
    
    return {
        'application_id': application_id,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'ssn': ssn,
        'date_of_birth': date_of_birth,
        'street': street,
        'city': city,
        'state': state,
        'zip': zip_code,
        'employer_name': employer_name,
        'job_title': job_title,
        'employment_status': employment_status,
        'annual_income': annual_income,
        'years_employed': years_employed,
        'employer_phone': employer_phone,
        'current_landlord': current_landlord,
        'current_landlord_phone': current_landlord_phone,
        'monthly_rent': monthly_rent,
        'years_at_current': years_at_current,
        'reason_for_leaving': reason_for_leaving,
        'pets': pets,
        'smoker': smoker,
        'bankruptcy_history': bankruptcy_history,
        'eviction_history': eviction_history,
        'status': status,
        'screening_completed': screening_completed,
        'application_data': json.dumps(application_data),
        'final_decision': json.dumps(final_decision) if final_decision else None,
        'decision_reason': decision_reason,
        'risk_score': risk_score,
        'created_at': created_at,
        'screened_at': screened_at
    }


def create_database():
    """Create database if it doesn't exist."""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
        connection.close()
        print(f"✓ Database '{DB_CONFIG['database']}' ready")
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        raise


def check_tables_exist(connection):
    """Check if application tables already exist."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'applications'")
            applications_exists = cursor.fetchone() is not None
            
            cursor.execute("SHOW TABLES LIKE 'agent_results'")
            agent_results_exists = cursor.fetchone() is not None
            
            return applications_exists and agent_results_exists
    except Exception as e:
        print(f"✗ Error checking tables: {e}")
        return False


def get_table_counts(connection):
    """Get count of records in applications table."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM applications")
            return cursor.fetchone()[0]
    except:
        return 0


def create_tables(connection):
    """Create tables from schema.sql."""
    print("\n📋 Creating database schema...")
    
    with connection.cursor() as cursor:
        # Read and execute schema
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            
            # Remove comments and split by semicolons properly
            statements = []
            current_statement = []
            
            for line in schema_sql.split('\n'):
                # Skip comment-only lines
                stripped = line.strip()
                if not stripped or stripped.startswith('--'):
                    continue
                
                # Remove inline comments
                if '--' in line:
                    line = line[:line.index('--')]
                
                current_statement.append(line)
                
                # Check if statement ends with semicolon
                if ';' in line:
                    stmt = '\n'.join(current_statement)
                    # Split by semicolon and add each part
                    parts = stmt.split(';')
                    for part in parts:
                        if part.strip():
                            statements.append(part.strip())
                    current_statement = []
            
            # Execute each statement
            for i, statement in enumerate(statements, 1):
                if statement.strip():
                    try:
                        # Skip CREATE USER and GRANT statements
                        if 'CREATE USER' in statement.upper() or 'GRANT' in statement.upper():
                            continue
                        
                        cursor.execute(statement)
                        connection.commit()
                        
                        # Show progress for table creation
                        if 'CREATE TABLE' in statement.upper():
                            table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                            print(f"  ✓ Created table: {table_name}")
                        elif 'DROP TABLE' in statement.upper():
                            print(f"  ✓ Dropped existing tables")
                            
                    except Exception as e:
                        # Ignore errors about tables not existing when dropping
                        if 'DROP TABLE' not in statement.upper():
                            print(f"  ✗ Error executing statement {i}: {e}")
                            print(f"    Statement preview: {statement[:100]}...")
                            raise
        
        print("✓ Schema created successfully")


def init_database(mode=None):
    """Initialize database and populate with sample data.
    
    Args:
        mode: Optional mode for non-interactive use:
              'recreate' - Drop tables and recreate
              'append' - Keep tables and add 10 records
              'keep' - Keep existing data only
              None - Interactive mode with prompts
    """
    
    print("=" * 60)
    print("Equifax Agentic AI Screening - Database Initialization")
    print("=" * 60)
    
    # Create database
    create_database()
    
    # Connect to database
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print(f"✓ Connected to MySQL database")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        print("\nPlease update DB_CONFIG in this script with your MySQL credentials")
        return
    
    try:
        # Check if tables already exist
        tables_exist = check_tables_exist(connection)
        existing_count = get_table_counts(connection) if tables_exist else 0
        
        if tables_exist:
            print(f"\n⚠️  Tables already exist with {existing_count} records")
            
            # Determine choice from mode or interactive prompt
            if mode == 'recreate':
                choice = '1'
                print("Mode: Recreate (drop and recreate tables)")
            elif mode == 'append':
                choice = '2'
                print("Mode: Append (add 10 more records)")
            elif mode == 'keep':
                choice = '3'
                print("Mode: Keep (no changes)")
            else:
                # Interactive mode
                print("\nChoose an option:")
                print("  1. Drop tables and recreate (⚠️  deletes all data)")
                print("  2. Keep existing tables and add 10 more sample records")
                print("  3. Keep existing data only (no changes)")
                print("  4. Exit")
                
                while True:
                    choice = input("\nEnter choice (1-4): ").strip()
                    if choice in ['1', '2', '3', '4']:
                        break
                    print("Invalid choice. Please enter 1, 2, 3, or 4")
            
            if choice == '1':
                print("\n⚠️  Dropping existing tables...")
                create_tables(connection)
                should_insert = True
                insert_count = 10
            elif choice == '2':
                print("\n✓ Keeping existing tables, will add 10 new records...")
                should_insert = True
                insert_count = 10
            elif choice == '3':
                print("\n✓ Keeping existing data, no changes made")
                should_insert = False
            else:  # choice == '4'
                print("\n✓ Exiting without changes")
                return
        else:
            print("\n📋 No existing tables found")
            create_tables(connection)
            should_insert = True
            insert_count = 10
        
        # Insert data if needed
        if should_insert:
            with connection.cursor() as cursor:
                # Generate applicants
                print(f"\n👥 Generating {insert_count} applicant records...")
                
                applicants = []
                
                # Calculate distribution for 10 records: 2 approved, 2 rejected, 6 pending
                approved_count = max(1, int(insert_count * 0.2))
                rejected_count = max(1, int(insert_count * 0.2))
                pending_count = insert_count - approved_count - rejected_count
                
                # Generate records
                print(f"  - {approved_count} approved applications...")
                for _ in range(approved_count):
                    applicants.append(generate_applicant_data('approved', 1))
                
                print(f"  - {rejected_count} rejected applications...")
                for _ in range(rejected_count):
                    applicants.append(generate_applicant_data('rejected', 1))
                
                print(f"  - {pending_count} pending applications...")
                for _ in range(pending_count):
                    applicants.append(generate_applicant_data('pending', 0))
                
                # Shuffle to mix statuses
                random.shuffle(applicants)
                
                # Insert applicants
                print("\n💾 Inserting records into database...")
                
                insert_query = """
                    INSERT INTO applications (
                        application_id, first_name, last_name, email, phone, ssn, date_of_birth,
                        street, city, state, zip, employer_name, job_title, employment_status,
                        annual_income, years_employed, employer_phone, current_landlord,
                        current_landlord_phone, monthly_rent, years_at_current, reason_for_leaving,
                        pets, smoker, bankruptcy_history, eviction_history, status, screening_completed,
                        application_data, final_decision, decision_reason, risk_score, created_at, screened_at
                    ) VALUES (
                        %(application_id)s, %(first_name)s, %(last_name)s, %(email)s, %(phone)s,
                        %(ssn)s, %(date_of_birth)s, %(street)s, %(city)s, %(state)s, %(zip)s,
                        %(employer_name)s, %(job_title)s, %(employment_status)s, %(annual_income)s,
                        %(years_employed)s, %(employer_phone)s, %(current_landlord)s,
                        %(current_landlord_phone)s, %(monthly_rent)s, %(years_at_current)s,
                        %(reason_for_leaving)s, %(pets)s, %(smoker)s, %(bankruptcy_history)s,
                        %(eviction_history)s, %(status)s, %(screening_completed)s, %(application_data)s,
                        %(final_decision)s, %(decision_reason)s, %(risk_score)s, %(created_at)s, %(screened_at)s
                    )
                """
                
                batch_size = 50
                inserted = 0
                for i in range(0, len(applicants), batch_size):
                    batch = applicants[i:i+batch_size]
                    cursor.executemany(insert_query, batch)
                    connection.commit()
                    inserted += len(batch)
                    print(f"  ✓ Inserted {inserted}/{len(applicants)} records")
                
                print(f"✓ All {inserted} records inserted successfully")
        
        # Display statistics
        with connection.cursor() as cursor:
            print("\n" + "=" * 60)
            print("📊 DATABASE STATISTICS")
            print("=" * 60)
            
            cursor.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status ORDER BY status")
            results = cursor.fetchall()
            for status, count in results:
                print(f"  {status.upper():12} : {count:3} applications")
            
            cursor.execute("SELECT COUNT(*) as count FROM applications WHERE screening_completed = 1")
            completed = cursor.fetchone()[0]
            print(f"\n  COMPLETED   : {completed:3} screenings")
            
            cursor.execute("SELECT COUNT(*) as count FROM applications WHERE screening_completed = 0")
            pending = cursor.fetchone()[0]
            print(f"  PENDING     : {pending:3} screenings")
            
            cursor.execute("SELECT COUNT(*) as total FROM applications")
            total = cursor.fetchone()[0]
            print(f"  TOTAL       : {total:3} applications")
        
        print("\n" + "=" * 60)
        print("✅ Database initialization completed successfully!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("  1. Update .env file with DATABASE_URL")
        print("  2. Start API server: uvicorn api.main:app --reload")
        print("  3. Start background processor: python background_processor.py --mode continuous")
        print("  4. Submit test applications: python submit_new_application.py --count 3")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        connection.rollback()
    finally:
        connection.close()
        print("Database connection closed")


if __name__ == "__main__":
    import sys
    
    # Check for command line argument to skip prompts
    mode = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--help', '-h']:
            print("Usage: python database/init_db.py [--recreate|--append|--keep]")
            print()
            print("Options:")
            print("  --recreate  : Drop existing tables and recreate (⚠️  deletes all data)")
            print("  --append    : Keep existing tables and add 10 more records")
            print("  --keep      : Keep existing data without changes")
            print("  (no args)   : Interactive mode with prompts")
            print()
            print("Examples:")
            print("  python database/init_db.py              # Interactive mode")
            print("  python database/init_db.py --recreate   # Fresh start")
            print("  python database/init_db.py --append     # Add more test data")
            sys.exit(0)
        elif arg == '--recreate':
            mode = 'recreate'
        elif arg == '--append':
            mode = 'append'
        elif arg == '--keep':
            mode = 'keep'
        else:
            print(f"Unknown option: {arg}")
            print("Use --help for usage information")
            sys.exit(1)
    
    init_database(mode)
