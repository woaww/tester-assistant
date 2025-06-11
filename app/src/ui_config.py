from src.models import AppSettingsParamConfig, ModelParamsConfig
from src.numerical_constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_REPETITION_PENALTY,
    DEFAULT_FREQUENCY_PENALTY
)
from src.text_constants import (
    LABEL_FOR_TEMPERATURE,
    DESCRIPTION_FOR_TEMPRATURE,
    SELECT_TEMPERATURE_STR,

    LABEL_FOR_MAX_NEW_TOKENS,
    DESCRIPTION_FOR_MAX_NEW_TOKENS,
    SELECT_MAX_NEW_TOKENS_STR,

    LABEL_FOR_REPETITION_PENALTY,
    DESCRIPTION_FOR_REPETITION_PENALTY,
    SELECT_REPETITION_PENALTY_STR,

    LABEL_FOR_FREQUENCY_PENALTY,
    DESCRIPTION_FOR_FREQUENCY_PENALTY,
    SELECT_FREQUENCY_PENALTY_STR
)

import numpy as np
# from dotenv import load_dotenv
# import os
# load_dotenv()

# WIKI_TOKEN = os.getenv('WIKI_TOKEN')

def make_temperature_config():
    return AppSettingsParamConfig(
        label=LABEL_FOR_TEMPERATURE,
        description=DESCRIPTION_FOR_TEMPRATURE,
        select=SELECT_TEMPERATURE_STR,
        options=[x / 10.0 for x in range(1, 11)],
        default=DEFAULT_TEMPERATURE
    )

def make_max_new_tokens_config():
    return AppSettingsParamConfig(
        label=LABEL_FOR_MAX_NEW_TOKENS,
        description=DESCRIPTION_FOR_MAX_NEW_TOKENS,
        select=SELECT_MAX_NEW_TOKENS_STR,
        options=list(range(50, 3001, 10)),
        default=DEFAULT_MAX_NEW_TOKENS
    )

def make_repetition_penalty_config():
    return AppSettingsParamConfig(
        label=LABEL_FOR_REPETITION_PENALTY,
        description=DESCRIPTION_FOR_REPETITION_PENALTY,
        select=SELECT_REPETITION_PENALTY_STR,
        options=np.round(np.arange(1.0, 2.05, 0.05), 2).tolist(),
        default=DEFAULT_REPETITION_PENALTY
    )

def make_frequency_penalty_config():
    return AppSettingsParamConfig(
        label=LABEL_FOR_FREQUENCY_PENALTY,
        description=DESCRIPTION_FOR_FREQUENCY_PENALTY,
        select=SELECT_FREQUENCY_PENALTY_STR,
        options=np.round(np.arange(0.1, 0.9, 0.05), 2).tolist(),
        default=DEFAULT_FREQUENCY_PENALTY
    )


def get_full_params_config():
    return ModelParamsConfig(
        temperature=make_temperature_config(),
        max_new_tokens=make_max_new_tokens_config(),
        repetition_penalty=make_repetition_penalty_config(),
        frequency_penalty=make_frequency_penalty_config()
    )