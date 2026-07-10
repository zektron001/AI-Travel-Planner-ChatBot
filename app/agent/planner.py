from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

from app.tools.weather import get_weather
from app.tools.travel import search_hotels, search_flights
from app.tools.search import search_attractions, multi_hop_search
from app.memory.manager import memory_manager

import os

SYSTEM_PROMPT = """You are an expert AI travel planner. Your job is to help users plan a personalized 2-day trip to any real city in earth.

DESTINATION GUARDRAIL — check this BEFORE anything else:
- Only plan trips to real, publicly accessible destinations on Earth
  reachable by commercial travel.
- If the destination is fictional, another planet, or not commercially
  reachable (e.g. Mars, Hogwarts, the Moon), do NOT create an itinerary
  and do NOT call any tools. Politely explain you only plan real-world
  trips, then suggest a real alternative with a similar vibe
  (for Mars: the Atacama Desert in Chile or Wadi Rum in Jordan).
- If unsure whether a destination is real, use multi_hop_search to
  verify it exists before planning anything.
  
You have access to these tools:
- multi_hop_search: Use this FIRST for any new destination — it does 3 chained searches (overview → districts → specific experiences) to build a rich knowledge base
- search_attractions: Use for specific follow-up searches (restaurants, activities, tips)
- get_weather: Check current weather at the destination
- search_hotels: Find available hotels (filter by budget)
- search_flights: Find available flights to the destination

Your planning approach:
1. When user mentions a destination, ALWAYS call multi_hop_search first to gather deep context
2. Then call get_weather, search_hotels, search_flights
3. Build a detailed 2-day itinerary with morning/afternoon/evening slots
4. Add local tips, cultural notes, and budget breakdown

Always:
- Ask clarifying questions if preferences are unclear
- Consider budget, dietary, accessibility constraints
- Be friendly and conversational
- Use emojis to make the plan visually appealing
- Format the itinerary clearly with Day 1 and Day 2 sections

{long_term_memory}
"""


def build_agent():
    llm = ChatOpenAI(
        model="gpt-4o", temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    tools = [
        multi_hop_search,
        search_attractions,
        get_weather,
        search_hotels,
        search_flights,
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)
    return executor


def chat(session_id: str, user_message: str) -> str:
    long_term = memory_manager.get_relevant_preferences(user_message)
    kb_context = memory_manager.search_knowledge_base(user_message)
    if kb_context:
        long_term = kb_context + "\n" + long_term

    agent_executor = build_agent()

    history = memory_manager.get_history(session_id)
    lc_history = []
    for msg in history:
        if msg["role"] == "user":
            lc_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_history.append(AIMessage(content=msg["content"]))

    response = agent_executor.invoke(
        {
            "input": user_message,
            "chat_history": lc_history,
            "long_term_memory": long_term,
        }
    )

    reply = response.get(
        "output", "Sorry, I couldn't generate a response. Please try again."
    )

    memory_manager.add_message(session_id, "user", user_message)
    memory_manager.add_message(session_id, "assistant", reply)

    preference_keywords = [
        "budget",
        "prefer",
        "like",
        "hate",
        "allergic",
        "vegetarian",
        "vegan",
        "pet",
        "family",
        "solo",
        "couple",
        "wheelchair",
        "luxury",
    ]
    if any(kw in user_message.lower() for kw in preference_keywords):
        memory_manager.save_preference(session_id, f"User said: {user_message}")

    return reply
