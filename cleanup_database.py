#!/usr/bin/env python3
"""
Script to cleanup database constraints for task_deadline_reminder module
Run this script to remove problematic foreign key constraints
"""

import psycopg2
import sys

def cleanup_constraints():
    # Database connection parameters - adjust as needed
    db_params = {
        'dbname': 'kodingyuk-db-odoo',
        'user': 'odoo17',
        'password': '',  # Add password if needed
        'host': 'localhost',
        'port': '5432'
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Drop the problematic foreign key constraint
        drop_constraint_query = """
        ALTER TABLE res_config_settings 
        DROP CONSTRAINT IF EXISTS res_config_settings_task_reminder_email_from_fkey;
        """
        
        cursor.execute(drop_constraint_query)
        conn.commit()
        
        print("Successfully dropped foreign key constraint")
        
        # Check if column exists and modify if needed
        check_column_query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'res_config_settings' 
        AND column_name = 'task_reminder_email_from';
        """
        
        cursor.execute(check_column_query)
        result = cursor.fetchone()
        
        if result:
            print(f"Column task_reminder_email_from exists with type: {result[1]}")
            if result[1] != 'character varying':
                modify_column_query = """
                ALTER TABLE res_config_settings 
                ALTER COLUMN task_reminder_email_from TYPE VARCHAR(255);
                """
                cursor.execute(modify_column_query)
                conn.commit()
                print("Modified column type to VARCHAR(255)")
        
        cursor.close()
        conn.close()
        
        print("Database cleanup completed successfully!")
        
    except Exception as e:
        print(f"Error during database cleanup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    cleanup_constraints()
