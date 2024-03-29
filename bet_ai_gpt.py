from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory, FileChatMessageHistory
import streamlit as st
from streamlit_chat import message
import os
from dotenv import load_dotenv, find_dotenv
import string

load_dotenv(find_dotenv(), override=True)

st.set_page_config(
  page_title='Your Custom Soccer Prophet',
  page_icon='🎲'
)

st.image('logo.png')
st.subheader('Even the surest bet holds a hint of uncertainty 🤞🏾🍀')

chat = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
history = FileChatMessageHistory('chat_history.json')
memory = ConversationBufferMemory(memory_key='chat_history', chat_memory=history, return_messages=True)

st.session_state.messages = st.session_state.get('messages', [])

page_button_style = f"""
<style>

button:focus {{
    border-color: rgba(250, 250, 250, 0.2) !important;
    color: white !important;
}}

button:hover {{
    color: green !important;
    border-color: green !important;
}}

</style>
"""

st.markdown(page_button_style, unsafe_allow_html=True)

with st.sidebar:
    api_key = st.text_input('OpenAI API key:', type='password')
    if api_key: os.environ['OPEN_AI_APIKEY'] = api_key

    team_1 = string.capwords(st.text_input(label='Enter the name of the first team'))
    team_2 = string.capwords(st.text_input(label='Enter the name of the second team').capitalize())
    forcast = st.button('Predict')

    if team_1 and team_2 and forcast:
        content = f"""If {team_1} and {team_2} play a soccer match today, based on the scores of \
their previous games, guess the scores? I don't need any explanation. Follow this rule of chain:\
1. If any of the teams/countries/clubs is not existent, tell me.\
2. If any of the teams/countries/clubs has a typo or is misspelled, suggest the correct name(s) to me instead of predicting the score.\
3. Otherwise, just give me the score as team_1 vs team_2: x-x"""
        
        prompt = ChatPromptTemplate(
            input_variables=['content'],
            messages=[
                SystemMessage(content='You are an expert soccer analyst.'),
                MessagesPlaceholder(variable_name='chat_history'),
                HumanMessagePromptTemplate.from_template('{content}')
            ]
        )

        human_message = f'{team_1} vs {team_2}'
        reversed_human_message = f'{team_2} vs {team_1}'

        if (human_message in st.session_state.messages):
            message_index = st.session_state.messages.index(human_message)
            ai_message = f'You already asked this earlier. {st.session_state.messages[message_index + 1]}'

        elif (reversed_human_message in st.session_state.messages):
            message_index = st.session_state.messages.index(reversed_human_message)
            ai_message = f'This is the same as {reversed_human_message} which I earlier predicted to be {st.session_state.messages[message_index + 1]}'

        elif any(team_1 in msg for msg in st.session_state.messages) and any(team_2 in msg for msg in st.session_state.messages):
            for msg in st.session_state.messages:
                if (team_1 in msg and team_2 in msg):
                    ai_message = f'The result of this match has been earlier forecasted. {msg}'
                    break
    
        else:
            with st.spinner('Forecasting the match results...'):
                chain = LLMChain(llm=chat, prompt=prompt, memory=memory, verbose=False)
                response = chain.invoke({'content': content})
                ai_message = response['text']
                teams = ai_message.split(":")[0]
                actual_teams = teams.split(" vs ")
                actual_teams
                teams_reversed = f'{actual_teams[1]} vs {actual_teams[0]}'
                for msg in st.session_state.messages:
                    if (teams in msg or teams_reversed in msg):
                        ai_message = f'Remember I earlier predicted this? {msg}'
                        break

        st.session_state.messages.append(human_message)
        st.session_state.messages.append(ai_message)

for i, msg in enumerate(st.session_state.messages):
    # remember i starts from 0
    is_user = True if (i % 2) == 0 else False
    message(msg, is_user=is_user, key=i)

# st.session_state