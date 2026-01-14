"""
Parser de intenciones y extracción de entidades
Detecta intenciones y extrae información de texto en español
"""
import re
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import dateparser
from rapidfuzz import fuzz
import config
import database

logger = logging.getLogger(__name__)


class IntentParser:
    """Parser de intenciones y entidades"""
    
    # Patrones de intenciones
    INTENT_PATTERNS = {
        'CREAR': [
            r'\b(crear|nueva|nuevo|añadir|agregar|añade|agrega)\b.*\b(tarea|recordar|recordatorio|recordarme)\b',
            r'\b(tarea|recordar|recordatorio)\b.*\b(crear|nueva|nuevo|añadir|agregar)\b',
        ],
        'LISTAR': [
            r'\b(listar|mostrar|ver|muestra|muéstrame|listar|lista)\b.*\b(tarea|tareas|pendiente|pendientes)\b',
            r'\b(tarea|tareas)\b.*\b(pendiente|pendientes|hoy|mañana|semana)\b',
        ],
        'CERRAR': [
            r'\b(cerrar|completar|hecha|terminada|terminar|completa|da por hecha|marcar como)\b.*\b(tarea|tareas)\b',
            r'\b(tarea|tareas)\b.*\b(cerrar|completar|hecha|terminada)\b',
        ],
        'REPROGRAMAR': [
            r'\b(cambiar|mover|reprogramar|posponer|adelantar)\b.*\b(fecha|tarea)\b',
            r'\b(fecha)\b.*\b(cambiar|mover|reprogramar)\b',
        ],
        'AMPLIAR': [
            r'\b(ampliar|ampliación|amplía|añadir|agregar)\b.*\b(tarea|información|detalle)\b',
            r'\b(tarea)\b.*\b(ampliar|ampliación|amplía)\b',
        ],
    }
    
    # Palabras clave de prioridad
    PRIORITY_KEYWORDS = {
        'urgent': ['urgente', 'urgent', 'inmediato', 'inmediata', 'ya', 'ahora'],
        'high': ['importante', 'importante', 'alta', 'high', 'prioritario'],
        'low': ['baja', 'low', 'poco importante', 'sin prisa'],
    }
    
    # Patrones para detectar cliente
    CLIENT_PATTERNS = [
        r'\b(?:cliente|del cliente|para el cliente|con el cliente)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)',
        r'\bcliente\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+)',
    ]
    
    def __init__(self, db: database.Database = None):
        self.db = db or database.Database()
    
    def parse(self, text: str) -> Dict:
        """
        Parsea texto y detecta intención + entidades
        
        Returns:
            Dict con:
            - intent: str (CREAR, LISTAR, CERRAR, etc.)
            - confidence: float (0-1)
            - entities: dict con cliente, fecha, prioridad, título
        """
        text = text.lower().strip()
        logger.info(f"Parseando texto: {text}")
        
        # Detectar intención
        intent, confidence = self._detect_intent(text)
        
        # Extraer entidades según intención
        entities = {}
        if intent == 'CREAR':
            entities = self._extract_create_entities(text)
        elif intent == 'LISTAR':
            entities = self._extract_list_entities(text)
        elif intent == 'CERRAR':
            entities = self._extract_close_entities(text)
        elif intent == 'REPROGRAMAR':
            entities = self._extract_reprogram_entities(text)
        elif intent == 'AMPLIAR':
            entities = self._extract_ampliar_entities(text)
        
        result = {
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'original_text': text
        }
        
        logger.info(f"Resultado del parseo: {result}")
        return result
    
    def _detect_intent(self, text: str) -> Tuple[str, float]:
        """Detecta la intención principal"""
        best_intent = 'UNKNOWN'
        best_confidence = 0.0
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = len(match.group()) / len(text)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        # Si no hay match claro, intentar inferir por palabras clave
        if best_intent == 'UNKNOWN':
            if any(word in text for word in ['tarea', 'recordar', 'recordatorio']):
                if any(word in text for word in ['crear', 'nueva', 'añadir']):
                    best_intent = 'CREAR'
                    best_confidence = 0.5
                elif any(word in text for word in ['listar', 'mostrar', 'ver']):
                    best_intent = 'LISTAR'
                    best_confidence = 0.5
        
        return best_intent, best_confidence
    
    def _extract_create_entities(self, text: str) -> Dict:
        """Extrae entidades para crear tarea"""
        entities = {}
        
        # Extraer cliente
        client = self._extract_client(text)
        if client:
            entities['client'] = client
        
        # Extraer fecha
        date = self._extract_date(text)
        if date:
            entities['due_date'] = date
        
        # Extraer prioridad
        priority = self._extract_priority(text)
        if priority:
            entities['priority'] = priority
        
        # Extraer título (texto restante después de limpiar entidades)
        title = self._extract_title(text, entities)
        if title:
            entities['title'] = title
        
        return entities
    
    def _extract_list_entities(self, text: str) -> Dict:
        """Extrae entidades para listar tareas"""
        entities = {}
        
        # Detectar filtro de fecha
        date = self._extract_date(text)
        if date:
            entities['due_date'] = date
        
        # Detectar filtro de cliente
        client = self._extract_client(text)
        if client:
            entities['client'] = client
        
        return entities
    
    def _extract_close_entities(self, text: str) -> Dict:
        """Extrae entidades para cerrar tarea"""
        entities = {}
        
        # Intentar extraer ID de tarea o cliente
        client = self._extract_client(text)
        if client:
            entities['client'] = client
        
        # Buscar número de tarea
        task_id_match = re.search(r'\b(tarea|tareas)\s+(\d+)', text)
        if task_id_match:
            entities['task_id'] = int(task_id_match.group(2))
        
        return entities
    
    def _extract_reprogram_entities(self, text: str) -> Dict:
        """Extrae entidades para reprogramar"""
        entities = {}
        
        # Extraer nueva fecha
        date = self._extract_date(text)
        if date:
            entities['due_date'] = date
        
        # Extraer ID de tarea o cliente
        client = self._extract_client(text)
        if client:
            entities['client'] = client
        
        task_id_match = re.search(r'\b(tarea|tareas)\s+(\d+)', text)
        if task_id_match:
            entities['task_id'] = int(task_id_match.group(2))
        
        return entities
    
    def _extract_ampliar_entities(self, text: str) -> Dict:
        """Extrae entidades para ampliar tarea"""
        entities = {}
        
        # Extraer ID de tarea
        task_id_match = re.search(r'\b(tarea|tareas)\s+(\d+)', text)
        if task_id_match:
            entities['task_id'] = int(task_id_match.group(2))
        
        return entities
    
    def _extract_client(self, text: str) -> Optional[Dict]:
        """Extrae información del cliente con fuzzy matching"""
        # Buscar patrón "cliente X"
        for pattern in self.CLIENT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                client_name = match.group(1).strip()
                return self._fuzzy_match_client(client_name)
        
        # Buscar nombres propios (palabras con mayúscula inicial)
        words = text.split()
        potential_names = []
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Agregar palabras consecutivas con mayúscula
                name_parts = [word]
                for j in range(i + 1, len(words)):
                    if words[j][0].isupper() or words[j].islower():
                        name_parts.append(words[j])
                    else:
                        break
                if len(name_parts) >= 1:
                    potential_names.append(' '.join(name_parts))
        
        # Probar con nombres potenciales
        for name in potential_names:
            client = self._fuzzy_match_client(name)
            if client:
                return client
        
        return None
    
    def _fuzzy_match_client(self, name: str) -> Optional[Dict]:
        """Busca cliente con fuzzy matching"""
        clients = self.db.search_clients()
        if not clients:
            return {'name': name, 'needs_creation': True}
        
        best_match = None
        best_score = 0.0
        
        for client in clients:
            score = fuzz.ratio(name.lower(), client['name'].lower()) / 100.0
            if score > best_score:
                best_score = score
                best_match = client
        
        if best_match:
            if best_score >= config.FUZZY_MATCH_THRESHOLD_AUTO:
                return {'id': best_match['id'], 'name': best_match['name'], 'confidence': best_score}
            elif best_score >= config.FUZZY_MATCH_THRESHOLD_CONFIRM:
                return {'id': best_match['id'], 'name': best_match['name'], 
                       'confidence': best_score, 'needs_confirmation': True}
        
        return {'name': name, 'needs_creation': True}
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extrae fecha usando dateparser"""
        # Palabras clave de tiempo relativo
        time_keywords = {
            'hoy': datetime.now(),
            'mañana': datetime.now() + timedelta(days=1),
            'pasado mañana': datetime.now() + timedelta(days=2),
            'ayer': datetime.now() - timedelta(days=1),
        }
        
        text_lower = text.lower()
        for keyword, date in time_keywords.items():
            if keyword in text_lower:
                return date.strftime('%Y-%m-%d')
        
        # Usar dateparser para fechas más complejas
        try:
            parsed_date = dateparser.parse(text, languages=['es'], settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.now()
            })
            if parsed_date:
                return parsed_date.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Error parseando fecha: {e}")
        
        return None
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """Extrae prioridad de palabras clave"""
        text_lower = text.lower()
        
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return priority
        
        return None
    
    def _extract_title(self, text: str, entities: Dict) -> str:
        """Extrae título limpiando entidades ya detectadas"""
        title = text
        
        # Eliminar palabras de intención
        intent_words = ['crear', 'nueva', 'nuevo', 'añadir', 'agregar', 'tarea', 
                       'recordar', 'recordatorio']
        for word in intent_words:
            title = re.sub(r'\b' + word + r'\b', '', title, flags=re.IGNORECASE)
        
        # Eliminar información de cliente
        if 'client' in entities:
            client_name = entities['client'].get('name', '')
            title = re.sub(r'\bcliente\s+' + re.escape(client_name), '', title, flags=re.IGNORECASE)
            title = re.sub(r'\b' + re.escape(client_name), '', title, flags=re.IGNORECASE)
        
        # Eliminar palabras de fecha
        date_words = ['hoy', 'mañana', 'pasado mañana', 'ayer', 'lunes', 'martes', 
                     'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
        for word in date_words:
            title = re.sub(r'\b' + word + r'\b', '', title, flags=re.IGNORECASE)
        
        # Eliminar palabras de prioridad
        priority_words = ['urgente', 'importante', 'alta', 'baja', 'prioridad']
        for word in priority_words:
            title = re.sub(r'\b' + word + r'\b', '', title, flags=re.IGNORECASE)
        
        # Limpiar espacios múltiples
        title = ' '.join(title.split())
        
        return title.strip() if title.strip() else text.strip()

