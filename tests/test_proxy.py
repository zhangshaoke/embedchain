import pytest
from unittest.mock import Mock, patch

from mem0.configs.prompts import MEMORY_ANSWER_PROMPT
from mem0 import Memory, MemoryClient, Mem0
from mem0.proxy.main import Chat, Completions

@pytest.fixture
def mock_memory_client():
    return Mock(spec=MemoryClient)

@pytest.fixture
def mock_openai_embedding_client():
    with patch('mem0.embeddings.openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_openai_llm_client():
    with patch('mem0.llms.openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_litellm():
    with patch('mem0.proxy.main.litellm') as mock:
        yield mock


def test_mem0_initialization_with_api_key(mock_openai_embedding_client, mock_openai_llm_client):
    mem0 = Mem0()
    assert isinstance(mem0.mem0_client, Memory)
    assert isinstance(mem0.chat, Chat)


def test_mem0_initialization_with_config():
    config = {"some_config": "value"}
    with patch('mem0.Memory.from_config') as mock_from_config:
        mem0 = Mem0(config=config)
        mock_from_config.assert_called_once_with(config)
        assert isinstance(mem0.chat, Chat)


def test_mem0_initialization_without_params(mock_openai_embedding_client, mock_openai_llm_client):
        mem0 = Mem0()
        assert isinstance(mem0.mem0_client, Memory)
        assert isinstance(mem0.chat, Chat)


def test_chat_initialization(mock_memory_client):
    chat = Chat(mock_memory_client)
    assert isinstance(chat.completions, Completions)


def test_completions_create(mock_memory_client, mock_litellm):
    completions = Completions(mock_memory_client)
    
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    mock_memory_client.search.return_value = [{"memory": "Some relevant memory"}]
    mock_litellm.completion.return_value = {"choices": [{"message": {"content": "I'm doing well, thank you!"}}]}
    
    response = completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        user_id="test_user",
        temperature=0.7
    )
    
    mock_memory_client.add.assert_called_once()
    mock_memory_client.search.assert_called_once()
    
    mock_litellm.completion.assert_called_once()
    call_args = mock_litellm.completion.call_args[1]
    assert call_args['model'] == "gpt-3.5-turbo"
    assert len(call_args['messages']) == 2 
    assert call_args['temperature'] == 0.7
    
    assert response == {"choices": [{"message": {"content": "I'm doing well, thank you!"}}]}


def test_completions_create_with_system_message(mock_memory_client, mock_litellm):
    completions = Completions(mock_memory_client)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    mock_memory_client.search.return_value = [{"memory": "Some relevant memory"}]
    mock_litellm.completion.return_value = {"choices": [{"message": {"content": "I'm doing well, thank you!"}}]}
    
    completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        user_id="test_user"
    )
    
    call_args = mock_litellm.completion.call_args[1]
    assert call_args['messages'][0]['role'] == "system"
    assert call_args['messages'][0]['content'] == MEMORY_ANSWER_PROMPT
