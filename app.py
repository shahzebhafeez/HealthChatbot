from flask import Flask, render_template, request, jsonify, session
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Sequence
from typing_extensions import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import trim_messages
import os
from dotenv import load_dotenv
import uuid


load_dotenv()

os.environ['GROQ_API_KEY']=os.getenv("GROQ_API_KEY")
os.environ['LANGSMITH_API_KEY']=os.getenv("LANGSMITH_API_KEY")
os.environ['LANGSMITH_TRACING']=os.getenv("LANGSMITH_TRACING")

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str
    
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You talk like a doctor, answer all the questions to the best of your abilities"
        ),
        MessagesPlaceholder(variable_name='messages')
    ]
)
model = init_chat_model("llama3-8b-8192",
                        model_provider='groq')
trimmer = trim_messages(
    max_tokens=65,
    strategy='last',
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on='human'
)
default_messages = [
    SystemMessage(content='You are a health information assistant. Provide helpful information about health conditions and diseases. Always remind users to consult healthcare professionals for medical advice.'),
    HumanMessage(content='Hello, I need some health information'),
    AIMessage(content='Hello! I can provide general information about health conditions. What would you like to know about?'),
    HumanMessage(content='What are the symptoms of diabetes?'),
    AIMessage(content='Common symptoms of diabetes include increased thirst, frequent urination, unexplained weight loss, fatigue, blurred vision, slow-healing sores, and frequent infections. There are different types of diabetes (Type 1, Type 2, gestational), each with varying symptom presentations. Remember to consult a healthcare provider if you experience these symptoms.'),
    HumanMessage(content='How is diabetes diagnosed?'),
    AIMessage(content='Diabetes is typically diagnosed through blood tests that measure blood glucose levels. These include fasting blood glucose tests, oral glucose tolerance tests, random blood glucose tests, and HbA1c tests that measure average blood sugar over 2-3 months. Early diagnosis is important for effective management.')
]
workflow = StateGraph(state_schema=State)
def call_model(state: State):
    trimmed_messages = trimmer.invoke(state["messages"])
    prompt = prompt_template.invoke(
        {"messages": trimmed_messages, "language": state["language"]}
    )
    response = model.invoke(prompt)
    return {"messages": [response]}

workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
memory = MemorySaver()
graph_app = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
language = "English"

def get_response_from_model(user_message):
    input_messages = default_messages + [HumanMessage(user_message)]
    print("input messages:",input_messages)
    try:
        output = graph_app.invoke(
            {"messages": input_messages,"language":language},
            config,
        )
        ai_response = output["messages"][-1].content
        return ai_response
    except Exception as e:
        print("error in response from model:",e)
        return f"error while getting response{e}"

app = Flask(__name__)
app.secret_key = "123xyzwasd" 

@app.route('/')
def index():
    if 'messages' not in session:
        session['messages'] = []
        for msg in default_messages:
            if msg.type == "system":
                continue
            entry = {
                'role': 'user' if msg.type == "human" else 'assistant',
                'content': msg.content
            }
            session['messages'].append(entry)
    
    return render_template('index.html', messages=session['messages'])

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['message']
    session['messages'].append({
        'role': 'user',
        'content': user_message
    })
    ai_response = get_response_from_model(user_message)
    session['messages'].append({
        'role': 'assistant',
        'content': ai_response
    })
    session.modified = True
    
    return jsonify({'message': ai_response})

if __name__ == '__main__':
    app.run(debug=True)
