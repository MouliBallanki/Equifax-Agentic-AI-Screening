# MySQL Setup Guide

## 1. Configure Database

Edit `database\init_db.py` - Update password:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_PASSWORD',  # Change this
    'database': 'equifax_screening',
    'charset': 'utf8mb4'
}
```

## 2. Initialize Database

```powershell
.\venv\Scripts\Activate.ps1
python database\init_db.py
```

Creates: 2 approved, 2 rejected, 6 pending applications

## 3. Start API Server

```powershell
uvicorn api.main:app --reload --port 8000
```

Access: http://localhost:8000/docs

## 4. Start Background Processor (Optional)

```powershell
.\venv\Scripts\Activate.ps1
python background_processor.py --mode continuous --batch-size 5 --poll-interval 10
```

## 5. Submit Applications

```powershell
python submit_new_application.py --count 5
```

## 6. Check Status

```powershell
python submit_new_application.py --stats
```

## SQL Commands

```sql
-- View pending
SELECT * FROM equifax_screening.applications WHERE status = 'PENDING';

-- Reset pending to unprocessed
UPDATE equifax_screening.applications 
SET screening_completed = 0 
WHERE status = 'PENDING';

-- Get statistics
SELECT status, screening_completed, COUNT(*) as count 
FROM equifax_screening.applications 
GROUP BY status, screening_completed;
```

## Troubleshooting

**MySQL not running:**
```powershell
Start-Service -Name MySQL80
```

**Module errors:**
```powershell
pip install -r requirements.txt
```
