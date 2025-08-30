"""
Reasoning Strategies Module for PIKE-RAG Web App
Implements different reasoning approaches: generation, self-ask, atomic decomposition
"""

import sys
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pikerag.workflows.common import GenerationQaData
from pikerag.prompts.qa.generation import generation_qa_protocol
from pikerag.prompts.self_ask.self_ask import self_ask_protocol
from pikerag.prompts.decomposition.atom_based import question_decompose_protocol

class BaseReasoningStrategy(ABC):
    """Base class for reasoning strategies"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def process_question(self, question: str, context: List[str], conversation_history: List[Dict[str, str]], llm_client, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a question using this reasoning strategy"""
        pass

class GenerationStrategy(BaseReasoningStrategy):
    """Simple generation strategy - direct question answering"""
    
    def __init__(self):
        super().__init__(
            name="generation",
            description="Direct question answering with retrieved context"
        )
    
    def process_question(self, question: str, context: List[str], conversation_history: List[Dict[str, str]], llm_client, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            qa_data = GenerationQaData(question=question)
            protocol = generation_qa_protocol
            
            # Include conversation history in the context
            messages = []
            
            # Add conversation history
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append(msg)
            
            # Process the current question
            current_messages = protocol.process_input(
                content=qa_data.question,
                references=context,
                **qa_data.as_dict()
            )
            
            # Combine history and current question
            if messages:
                # Add system message to maintain context
                system_msg = {
                    "role": "system", 
                    "content": "Continue the conversation naturally, taking into account the previous context."
                }
                final_messages = [system_msg] + messages + current_messages
            else:
                final_messages = current_messages
            
            response = llm_client.generate_content_with_messages(final_messages, **llm_config)
            output_dict = protocol.parse_output(response, **qa_data.as_dict())
            
            return {
                'success': True,
                'strategy': self.name,
                'answer': output_dict.get('answer', 'No answer generated'),
                'rationale': output_dict.get('rationale', ''),
                'raw_response': response,
                'reasoning_steps': [
                    f"Retrieved {len(context)} relevant documents",
                    f"Considered last {len(conversation_history)} conversation turns",
                    "Generated direct answer using context"
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'strategy': self.name,
                'error': str(e),
                'answer': f'Error in generation strategy: {str(e)}'
            }

class SelfAskStrategy(BaseReasoningStrategy):
    """Self-ask strategy - break down complex questions into sub-questions"""
    
    def __init__(self):
        super().__init__(
            name="self_ask",
            description="Break complex questions into sub-questions and answer step by step"
        )
    
    def process_question(self, question: str, context: List[str], conversation_history: List[Dict[str, str]], llm_client, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # For now, use a simplified approach with generation protocol
            # but add self-ask reasoning prompting
            qa_data = GenerationQaData(question=question)
            
            reasoning_steps = []
            reasoning_steps.append("Analyzing question complexity for self-ask reasoning")
            reasoning_steps.append("Breaking down question into sub-questions")
            reasoning_steps.append("Answering each sub-question systematically")
            
            # Create messages with self-ask prompting
            messages = []
            
            # Add conversation history
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                messages.append(msg)
            
            # Create a self-ask style prompt
            self_ask_prompt = f"""Break this question down using a step-by-step reasoning approach:

Question: {question}

Context: {' '.join(context) if context else 'No additional context provided.'}

Please follow this format:
1. Are follow-up questions needed? [Yes/No]
2. If yes, what sub-questions should we ask?
3. Answer each sub-question
4. Provide the final answer

Answer:"""
            
            messages.append({"role": "user", "content": self_ask_prompt})
            
            response = llm_client.generate_content_with_messages(messages, **llm_config)
            
            return {
                'success': True,
                'strategy': self.name,
                'answer': response,
                'rationale': 'Used self-ask reasoning to break down and answer the question step by step',
                'raw_response': response,
                'reasoning_steps': reasoning_steps
            }
            
        except Exception as e:
            return {
                'success': False,
                'strategy': self.name,
                'error': str(e),
                'answer': f'Error in self-ask strategy: {str(e)}'
            }

class AtomicDecompositionStrategy(BaseReasoningStrategy):
    """Atomic decomposition strategy - break questions into atomic facts"""
    
    def __init__(self):
        super().__init__(
            name="atomic_decomposition", 
            description="Decompose complex questions into atomic facts and reason systematically"
        )
    
    def process_question(self, question: str, context: List[str], conversation_history: List[Dict[str, str]], llm_client, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            reasoning_steps = []
            reasoning_steps.append("Decomposing question into atomic facts")
            reasoning_steps.append("Analyzing each atomic component against available context")
            reasoning_steps.append("Synthesizing atomic facts into comprehensive answer")
            
            # Create messages with atomic decomposition prompting
            messages = []
            
            # Add conversation history
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                messages.append(msg)
            
            # Create an atomic decomposition style prompt
            atomic_prompt = f"""Analyze this question using atomic decomposition - break it down into fundamental facts:

Question: {question}

Context: {' '.join(context) if context else 'No additional context provided.'}

Please follow this approach:
1. Identify the atomic facts (smallest units of information) needed to answer this question
2. For each atomic fact, determine if we can answer it from the context or need additional information
3. Build up the answer systematically from these atomic components
4. Provide a comprehensive final answer

Analysis:"""
            
            messages.append({"role": "user", "content": atomic_prompt})
            
            response = llm_client.generate_content_with_messages(messages, **llm_config)
            
            return {
                'success': True,
                'strategy': self.name,
                'answer': response,
                'rationale': 'Used atomic decomposition to systematically analyze and answer the question',
                'raw_response': response,
                'reasoning_steps': reasoning_steps
            }
            
        except Exception as e:
            return {
                'success': False,
                'strategy': self.name,
                'error': str(e),
                'answer': f'Error in atomic decomposition strategy: {str(e)}'
            }

class ReasoningStrategyManager:
    """Manager for different reasoning strategies"""
    
    def __init__(self):
        self.strategies = {
            'generation': GenerationStrategy(),
            'self_ask': SelfAskStrategy(),
            'atomic_decomposition': AtomicDecompositionStrategy()
        }
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseReasoningStrategy]:
        """Get a reasoning strategy by name"""
        return self.strategies.get(strategy_name)
    
    def list_strategies(self) -> List[Dict[str, str]]:
        """List all available strategies"""
        return [
            {
                'name': strategy.name,
                'description': strategy.description
            }
            for strategy in self.strategies.values()
        ]
    
    def process_with_strategy(self, strategy_name: str, question: str, context: List[str], conversation_history: List[Dict[str, str]], llm_client, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a question using the specified strategy"""
        strategy = self.get_strategy(strategy_name)
        
        if not strategy:
            return {
                'success': False,
                'error': f'Unknown reasoning strategy: {strategy_name}',
                'available_strategies': [s['name'] for s in self.list_strategies()]
            }
        
        return strategy.process_question(question, context, conversation_history, llm_client, llm_config)