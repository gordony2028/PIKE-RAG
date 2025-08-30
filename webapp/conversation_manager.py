"""
Conversation Management Module for PIKE-RAG Web App
Handles multi-turn conversations with memory
"""

import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class ConversationMessage:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ConversationSession:
    session_id: str
    created_at: str
    last_updated: str
    messages: List[ConversationMessage]
    context_summary: str = ""
    reasoning_strategy: str = "generation"
    knowledge_base: str = "documents"
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert messages to dict format
        data['messages'] = [msg.to_dict() for msg in self.messages]
        return data

class ConversationManager:
    def __init__(self, sessions_dir: str):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
        self._active_sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self, reasoning_strategy: str = "generation", knowledge_base: str = "documents") -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        session = ConversationSession(
            session_id=session_id,
            created_at=current_time,
            last_updated=current_time,
            messages=[],
            reasoning_strategy=reasoning_strategy,
            knowledge_base=knowledge_base,
            metadata={}
        )
        
        self._active_sessions[session_id] = session
        self._save_session(session)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a conversation session"""
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        # Try to load from disk
        session = self._load_session(session_id)
        if session:
            self._active_sessions[session_id] = session
        
        return session
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a message to a conversation session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_updated = datetime.now().isoformat()
        
        # Update context summary if needed
        if len(session.messages) > 10:  # Summarize after 10 messages
            self._update_context_summary(session)
        
        self._save_session(session)
        return True
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[ConversationMessage]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Return recent messages
        return session.messages[-limit:] if limit > 0 else session.messages
    
    def get_context_for_llm(self, session_id: str, include_summary: bool = True) -> List[Dict[str, str]]:
        """Get conversation context formatted for LLM"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = []
        
        # Add context summary if available and requested
        if include_summary and session.context_summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {session.context_summary}"
            })
        
        # Add recent conversation messages
        recent_messages = session.messages[-10:]  # Last 10 messages
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    def update_session_settings(self, session_id: str, reasoning_strategy: str = None, knowledge_base: str = None) -> bool:
        """Update session settings"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        if reasoning_strategy:
            session.reasoning_strategy = reasoning_strategy
        if knowledge_base:
            session.knowledge_base = knowledge_base
        
        session.last_updated = datetime.now().isoformat()
        self._save_session(session)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session"""
        # Remove from active sessions
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        # Remove from disk
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        try:
            if os.path.exists(session_file):
                os.remove(session_file)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all conversation sessions"""
        sessions = []
        
        # Get sessions from disk
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # Remove .json extension
                session = self._load_session(session_id)
                if session:
                    sessions.append({
                        'session_id': session.session_id,
                        'created_at': session.created_at,
                        'last_updated': session.last_updated,
                        'message_count': len(session.messages),
                        'reasoning_strategy': session.reasoning_strategy,
                        'knowledge_base': session.knowledge_base
                    })
        
        # Sort by last_updated
        sessions.sort(key=lambda x: x['last_updated'], reverse=True)
        return sessions
    
    def clear_old_sessions(self, days: int = 30) -> int:
        """Clear sessions older than specified days"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleared_count = 0
        
        for session_info in self.list_sessions():
            session_date = datetime.fromisoformat(session_info['last_updated'].replace('Z', '+00:00'))
            if session_date < cutoff_date:
                if self.delete_session(session_info['session_id']):
                    cleared_count += 1
        
        return cleared_count
    
    def _save_session(self, session: ConversationSession):
        """Save session to disk"""
        session_file = os.path.join(self.sessions_dir, f"{session.session_id}.json")
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load session from disk"""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        try:
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert message dicts back to ConversationMessage objects
                messages = []
                for msg_data in data.get('messages', []):
                    messages.append(ConversationMessage(
                        role=msg_data['role'],
                        content=msg_data['content'],
                        timestamp=msg_data['timestamp'],
                        metadata=msg_data.get('metadata', {})
                    ))
                
                session = ConversationSession(
                    session_id=data['session_id'],
                    created_at=data['created_at'],
                    last_updated=data['last_updated'],
                    messages=messages,
                    context_summary=data.get('context_summary', ''),
                    reasoning_strategy=data.get('reasoning_strategy', 'generation'),
                    knowledge_base=data.get('knowledge_base', 'documents'),
                    metadata=data.get('metadata', {})
                )
                
                return session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
        
        return None
    
    def _update_context_summary(self, session: ConversationSession):
        """Update context summary for long conversations"""
        if len(session.messages) <= 10:
            return
        
        # Simple summarization - in a production system, you'd use an LLM for this
        recent_topics = []
        for msg in session.messages[-10:]:
            if msg.role == 'user' and len(msg.content) > 20:
                # Extract key topics (simple keyword extraction)
                words = msg.content.lower().split()
                key_words = [w for w in words if len(w) > 4 and w.isalpha()][:3]
                if key_words:
                    recent_topics.extend(key_words)
        
        # Create summary
        if recent_topics:
            unique_topics = list(set(recent_topics))[:5]
            session.context_summary = f"Recent discussion topics: {', '.join(unique_topics)}"
        else:
            session.context_summary = f"Conversation with {len(session.messages)} messages"