import pandas as pd
import logging
from datetime import datetime
from ragtime.expe import Expe, QA, Question, Facts, Fact, Answer, LLMAnswer, Chunks, Chunk

def process_answer_file(file):
    """Process uploaded answer file"""
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        required_cols = ['question', 'answer']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("File must contain 'question' and 'answer' columns")
            
        return df.to_dict('records')
        
    except Exception as e:
        logging.error(f"Error processing answer file: {str(e)}")
        raise

def merge_answers_with_validation(validation_data, answers_data):
    """Merge validation set data with uploaded answers"""
    expe = Expe()
    
    for item in validation_data['items']:
        question_text = item['question']['text']
        matched_answer = next(
            (a for a in answers_data if a['question'].lower() == question_text.lower()),
            None
        )
        
        qa = QA(
            question=Question(text=question_text),
            facts=Facts(items=[Fact(text=f['text']) for f in item['facts']['items']])
        )
        
        if matched_answer:
            # Add uploaded answer
            answer = Answer(
                text=matched_answer['answer'],
                llm_answer=LLMAnswer(
                    name=matched_answer.get('model_name', 'Custom'),
                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                )
            )
            qa.answers.items.append(answer)
            
            # Add chunks if present
            chunks = [col for col in matched_answer.keys() if col.startswith('chunk_')]
            if chunks:
                qa.chunks = Chunks()
                for chunk in chunks:
                    if matched_answer[chunk]:
                        qa.chunks.items.append(Chunk(text=matched_answer[chunk]))
                
        expe.append(qa)
        
    return expe