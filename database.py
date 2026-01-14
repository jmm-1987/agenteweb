"""
Gestión de base de datos SQLite
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import config

logger = logging.getLogger(__name__)


class Database:
    """Gestor de base de datos SQLite"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.SQLITE_PATH
        self.init_db()
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Inicializa las tablas si no existen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de tareas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                client_id INTEGER,
                due_date DATE,
                priority TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                solution TEXT,
                ampliacion TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        ''')
        
        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_client_id ON tasks(client_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)')
        
        # Migración: añadir columnas si no existen
        self._migrate_schema(cursor)
        
        conn.commit()
        conn.close()
        logger.info(f"Base de datos inicializada en {self.db_path}")
    
    def _migrate_schema(self, cursor):
        """Migra el esquema añadiendo columnas faltantes"""
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'solution' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN solution TEXT')
            logger.info("Columna 'solution' añadida a tasks")
        
        if 'ampliacion' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN ampliacion TEXT')
            logger.info("Columna 'ampliacion' añadida a tasks")
    
    def add_client(self, name: str) -> int:
        """Añade un nuevo cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO clients (name) VALUES (?)', (name,))
            conn.commit()
            client_id = cursor.lastrowid
            logger.info(f"Cliente añadido: {name} (ID: {client_id})")
            return client_id
        except sqlite3.IntegrityError:
            # Cliente ya existe
            cursor.execute('SELECT id FROM clients WHERE name = ?', (name,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()
    
    def get_client_by_name(self, name: str) -> Optional[Dict]:
        """Obtiene un cliente por nombre exacto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_client_by_id(self, client_id: int) -> Optional[Dict]:
        """Obtiene un cliente por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def search_clients(self, query: str = None) -> List[Dict]:
        """Busca clientes (todos o filtrados)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if query:
            cursor.execute('SELECT * FROM clients WHERE name LIKE ? ORDER BY name', (f'%{query}%',))
        else:
            cursor.execute('SELECT * FROM clients ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def add_task(self, title: str, client_id: int = None, due_date: str = None, 
                 priority: str = 'normal') -> int:
        """Añade una nueva tarea"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, client_id, due_date, priority)
            VALUES (?, ?, ?, ?)
        ''', (title, client_id, due_date, priority))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        logger.info(f"Tarea añadida: {title} (ID: {task_id})")
        return task_id
    
    def get_tasks(self, status: str = None, client_id: int = None, 
                  due_date: str = None, limit: int = None) -> List[Dict]:
        """Obtiene tareas con filtros"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, c.name as client_name
            FROM tasks t
            LEFT JOIN clients c ON t.client_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND t.status = ?'
            params.append(status)
        
        if client_id:
            query += ' AND t.client_id = ?'
            params.append(client_id)
        
        if due_date:
            query += ' AND t.due_date = ?'
            params.append(due_date)
        
        query += ' ORDER BY t.due_date ASC, t.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task = dict(row)
            # Convertir fechas a strings
            if task.get('due_date'):
                task['due_date'] = str(task['due_date'])
            if task.get('created_at'):
                task['created_at'] = str(task['created_at'])
            if task.get('completed_at'):
                task['completed_at'] = str(task['completed_at'])
            tasks.append(task)
        
        return tasks
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Obtiene una tarea por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, c.name as client_name
            FROM tasks t
            LEFT JOIN clients c ON t.client_id = c.id
            WHERE t.id = ?
        ''', (task_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            task = dict(row)
            if task.get('due_date'):
                task['due_date'] = str(task['due_date'])
            if task.get('created_at'):
                task['created_at'] = str(task['created_at'])
            if task.get('completed_at'):
                task['completed_at'] = str(task['completed_at'])
            return task
        return None
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Actualiza una tarea"""
        allowed_fields = ['title', 'client_id', 'due_date', 'priority', 'status', 
                         'solution', 'ampliacion', 'completed_at']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [task_id]
        cursor.execute(f'UPDATE tasks SET {set_clause} WHERE id = ?', values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        logger.info(f"Tarea {task_id} actualizada: {updates}")
        return success
    
    def complete_task(self, task_id: int) -> bool:
        """Marca una tarea como completada"""
        return self.update_task(task_id, status='completed', 
                               completed_at=datetime.now().isoformat())
    
    def delete_task(self, task_id: int) -> bool:
        """Elimina una tarea"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        logger.info(f"Tarea {task_id} eliminada")
        return success
    
    def delete_client(self, client_id: int) -> bool:
        """Elimina un cliente (solo si no tiene tareas)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Verificar si tiene tareas
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE client_id = ?', (client_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        logger.info(f"Cliente {client_id} eliminado")
        return success

