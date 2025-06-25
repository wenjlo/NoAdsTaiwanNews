from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import LlamaCpp


def LargeLanguageModel(path):

    model = LlamaCpp(
        model_path=path,
        n_gpu_layers=0,
        n_batch=256,
        n_ctx=2048,
        f16_kv=True,
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        verbose=True
    )
    return model