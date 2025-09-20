import inspect

from dagster_project.resources.llm_provider import LLMProviderResource


def test_llm_provider_generate_is_synchronous():
    # Assert the method is a normal function (not a coroutine)
    assert not inspect.iscoroutinefunction(LLMProviderResource.generate)

