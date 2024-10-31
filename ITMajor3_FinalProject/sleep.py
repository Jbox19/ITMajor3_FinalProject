from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timedelta

database = 'sleep_sched.db'

def db_connection():
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    return connection

app = FastAPI()

class SleepLog(BaseModel):
    sleep_time: str  
    wake_time: str  
    duration: float   

class SleepGoal(BaseModel):
    year: int       
    month: int      
    hours_per_night: float

class DailySleepSummary(BaseModel):
    date: str  
    total_duration: float  
    log_count: int  

class MonthlySleepReport(BaseModel):
    year: int
    month: int
    total_sleep_duration: float
    average_sleep_duration: float
    achievement_message: str

class History(BaseModel):
    sleep_time: str  
    wake_time: str  
    duration: float  

class Recommendation(BaseModel):
    recommendation: str

@app.post("/sleep_logs")
async def add_sleep_log(log: SleepLog):
    sleep_time = datetime.strptime(log.sleep_time, '%Y-%m-%d %H:%M')
    wake_time = datetime.strptime(log.wake_time, '%Y-%m-%d %H:%M')
    duration = (wake_time - sleep_time).total_seconds() / 3600  

    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO sleep_logs (sleep_time, wake_time, duration)
            VALUES (?, ?, ?)
        """, (log.sleep_time, log.wake_time, duration))
        connection.commit()
        return {"message": "Sleep log added successfully!"}
    except Exception as e:
        connection.rollback(),
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@app.get("/sleep_logs")
async def get_all_sleep_logs():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sleep_logs")
        logs = cursor.fetchall()
        return [dict(log) for log in logs]
    finally:
        connection.close()

@app.get("/sleep_logs/{date}")
async def get_sleep_logs_by_date(date: str):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sleep_logs WHERE sleep_time LIKE ?", (f"{date}%",))
        logs = cursor.fetchall()
        return [dict(log) for log in logs] if logs else []
    finally:
        connection.close()

@app.put("/sleep_logs/{log_id}")
async def update_sleep_log(log_id: int, log: SleepLog):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id FROM sleep_logs WHERE id = ?", (log_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Sleep log not found")

        sleep_time = datetime.strptime(log.sleep_time, '%Y-%m-%d %H:%M')
        wake_time = datetime.strptime(log.wake_time, '%Y-%m-%d %H:%M')
        duration = (wake_time - sleep_time).total_seconds() / 3600  

        cursor.execute("""
            UPDATE sleep_logs
            SET sleep_time = ?, wake_time = ?, duration = ?
            WHERE id = ?
        """, (log.sleep_time, log.wake_time, duration, log_id))
        connection.commit()
        return {"message": "Sleep log updated successfully!"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@app.delete("/sleep_logs/{log_id}")
async def delete_sleep_log(log_id: int):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sleep_logs where id = ?", (log_id,))
        history = cursor.fetchone()
        cursor.execute("INSERT INTO history (sleep_time, wake_time, duration)VALUES(?, ?, ?)",(history[1], history[2], history[3]))
        cursor.execute("DELETE FROM sleep_logs WHERE id = ?", (log_id,))
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Sleep log not found")
        return {"message": "Sleep log deleted successfully!"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@app.get("/sleep_logs/average_duration")
async def get_average_sleep_duration():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT AVG(duration) as average_duration FROM sleep_logs")
        average_duration = cursor.fetchone()["average_duration"] or 0
        return {"average_sleep_duration": average_duration}
    finally:
        connection.close()

@app.get("/sleep_logs/frequent_sleep_time")
async def get_frequent_sleep_time():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT strftime('%H', sleep_time) as hour, COUNT(*) as count FROM sleep_logs GROUP BY hour ORDER BY count DESC LIMIT 1")
        frequent_time = cursor.fetchone()
        return {"frequent_sleep_hour": frequent_time["hour"], "count": frequent_time["count"]}
    finally:
        connection.close()

@app.get("/sleep_logs/frequent_wake_time")
async def get_frequent_wake_time():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT strftime('%H', wake_time) as hour, COUNT(*) as count FROM sleep_logs GROUP BY hour ORDER BY count DESC LIMIT 1")
        frequent_time = cursor.fetchone()
        return {"frequent_wake_hour": frequent_time["hour"], "count": frequent_time["count"]}
    finally:
        connection.close()

@app.get("/sleep_logs/longest_sleep")
async def get_longest_sleep_duration():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT MAX(duration) as longest_sleep FROM sleep_logs")
        longest_sleep = cursor.fetchone()["longest_sleep"] or 0
        return {"longest_sleep_duration": longest_sleep}
    finally:
        connection.close()

@app.get("/sleep_logs/shortest_sleep")
async def get_shortest_sleep_duration():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT MIN(duration) as shortest_sleep FROM sleep_logs")
        shortest_sleep = cursor.fetchone()["shortest_sleep"] or 0
        return {"shortest_sleep_duration": shortest_sleep}
    finally:
        connection.close()

@app.get("/sleep_logs/month/{year}/{month}")
async def get_sleep_logs_by_month(year: int, month: int):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT * FROM sleep_logs
            WHERE strftime('%Y', sleep_time) = ? AND strftime('%m', sleep_time) = ?
        """, (str(year), f"{month:02d}"))
        logs = cursor.fetchall()
        return [dict(log) for log in logs] if logs else []
    finally:
        connection.close()

@app.get("/sleep_logs/year/{year}")
async def get_sleep_logs_by_year(year: int):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sleep_logs WHERE strftime('%Y', sleep_time) = ?", (str(year),))
        logs = cursor.fetchall()
        return [dict(log) for log in logs] if logs else []
    finally:
        connection.close()

@app.post("/sleep_goals/monthly_sleep_goal")
async def set_monthly_sleep_goal(goal: SleepGoal):
    connection = db_connection()
    cursor = connection.cursor()
    
    days_in_month = (datetime(goal.year, goal.month + 1, 1) - timedelta(days=1)).day
    total_hours_required = goal.hours_per_night * days_in_month

    cursor.execute("""
        SELECT SUM(duration) AS total_sleep_duration
        FROM sleep_logs 
        WHERE strftime('%Y', sleep_time) = ? AND strftime('%m', sleep_time) = ?
    """, (str(goal.year), f"{goal.month:02d}"))
    total_logged_sleep = cursor.fetchone()["total_sleep_duration"] or 0

    if total_logged_sleep >= total_hours_required:
        message = f"You achieved your goal of sleeping {goal.hours_per_night} hours a day this month!"
    else:
        message = f"You didn't sleep well this month. Your goal was to sleep {total_hours_required} hours, but you only logged {total_logged_sleep:.2f} hours."

    return {"message": message, "total_logged_sleep": total_logged_sleep, "total_required_sleep": total_hours_required}

@app.get("/sleep_logs/summary/{date}")
async def get_daily_sleep_summary(date: str):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT SUM(duration) as total_duration, COUNT(*) as log_count FROM sleep_logs WHERE sleep_time LIKE ?", (f"{date}%",))
        summary = cursor.fetchone()
        
        total_duration = summary["total_duration"] or 0
        log_count = summary["log_count"] or 0
        average_duration = total_duration / log_count if log_count > 0 else 0
        
        return DailySleepSummary(
            date=date,
            total_duration=total_duration,
            average_duration=average_duration,
            log_count=log_count
        )
    finally:
        connection.close()

@app.get("sleep_logs/history")
async def get_all_sleep_logs():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM history")
        history = cursor.fetchall()
        return [dict(hist) for hist in history]
    finally:
        connection.close()

@app.post("/recommendations")
async def add_recommendations(recommendation: str):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO sleep_recommendations (recommendation) VALUES (?)", (recommendation,))
        connection.commit()
        return {"message": "Recommendation added successfully"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        connection.close()

@app.get("/recommendations")
async def recommendation_list():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sleep_recommendations")
        rec = cursor.fetchall()
        return [dict(reco) for reco in rec]
    finally:
        connection.close()

@app.put("/recommendations/{recommendation_id}")
async def update_recommendation(recommendation_id: int, new_recommendation: str):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE sleep_recommendations SET recommendation = ? WHERE id = ?", 
                       (new_recommendation, recommendation_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        connection.commit()
        return {"message": "Recommendation updated successfully"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        connection.close()

@app.delete("/recommendations/{recommendation_id}")
async def delete_recommendation(recommendation_id: int):
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM sleep_recommendations where id = ?", (recommendation_id,))
        rec = cursor.fetchone()
        cursor.execute("INSERT INTO recommendation_history(recommendation)VALUES(?)", (rec[1],))
        cursor.execute("DELETE FROM sleep_recommendations WHERE id = ?", (recommendation_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        connection.commit()
        return {"message": "Recommendation deleted successfully"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        connection.close()

@app.get("/recommendations/history")
async def get_all_sleep_logs():
    connection = db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM recommendation_history")
        rec_history = cursor.fetchall()
        return [dict(hist) for hist in rec_history]
    finally:
        connection.close()

if __name__ == "__main__":
    init_db()
