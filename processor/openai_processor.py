from .base_processor import BaseProcessor
import openai
from utils.helpers import retry_on_request


def openai_setup(secrets):
    openai.api_key = secrets


@retry_on_request
def _openai_api_caller(model, messages, functions, function_call):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        return response
    except openai.error.Timeout as e:
        print(f"OpenAI API request timed out: {e}")
        raise
    except openai.error.APIError as e:
        print(f"OpenAI API returned an API Error: {e}")
        raise
    except openai.error.APIConnectionError as e:
        print(f"OpenAI API request failed to connect: {e}")
        raise
    except openai.error.InvalidRequestError as e:
        print(f"OpenAI API request was invalid: {e}")
        raise
    except openai.error.AuthenticationError as e:
        print(f"OpenAI API request was not authorized: {e}")
        raise
    except openai.error.PermissionError as e:
        print(f"OpenAI API request was not permitted: {e}")
        raise
    except openai.error.RateLimitError as e:
        print(f"OpenAI API request exceeded rate limit: {e}")
        raise
    except openai.error.ServiceUnavailableError as e:
        print(f"The server is overloaded or not ready yet: {e}")
        raise


class OpenaiProcessor(BaseProcessor):
    def process(self):
        ...


def get_incorporation_entities(pdf_text):
    messages = [{"role": "user", "content": pdf_text}]
    functions = [
        {
            "name": "get_incorporation_entities",
            "description": "Identify the main entities, participants and events in a company incorporation legal text",
            "parameters": {
                "title": "Legal Document",
                "type": "object",
                "properties": {
                    "notary": {
                        "type": "string",
                    },
                    "parties": {
                        "type": "array",
                        "description": "The persons or companies that are incorporating a new company",
                        "items": {
                            "type": "object",
                            "properties": {
                                "EntityType": {
                                    "type": "string",
                                    "enum": ["Individual", "ExistingCompany"],
                                    "description": "Type of the incorporating entity, can be an individual or an existing company",
                                },
                                "EntityName": {
                                    "type": "string",
                                    "description": "the name of the individual or existing company that is incorporating a new company",
                                },
                                "TaxIdentifier": {
                                    "type": "string",
                                    "description": "the RUN, RUT, CI or tax ID of the individual or existing company that is incorporating a new company",
                                },
                                "OwnershipDetails": {
                                    "type": "string",
                                    "description": "Number of stocks or percentage of capital owned by individual or company",
                                },
                                "EntityAddress": {
                                    "type": "string",
                                    "description": "the personal address of the individual or existing company that is incorporating a new company",
                                },
                                "CompanyRepresentative": {
                                    "type": "string",
                                    "description": "if the incorporating entity is an existing company, name of the representative",
                                },
                            },
                        },
                    },
                    "company": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "capital": {"type": "number"},
                            "registryDetails": {"type": "string"},
                            "businessPurposeSummary": {
                                "type": "string",
                                "description": "Summary of the business purpose of the company in less than 10 words",
                            },
                        },
                        "required": ["name", "RUT", "capital", "registryDetails"],
                    },
                },
                "required": ["parties", "company"],
            },
        },
    ]
    response = _openai_api_caller(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call={
            "name": "get_incorporation_entities"
        },  # force to call specific function
    )
    response_message = {}

    response_message = response["choices"][0]["message"]["function_call"]["arguments"]

    return response_message


def get_modification_entities(pdf_text):
    messages = [{"role": "user", "content": pdf_text}]
    functions = [
        {
            "name": "get_modification_entities",
            "description": "Get the main participants in a legal text",
            "parameters": {
                "title": "Legal Document",
                "type": "object",
                "properties": {
                    "companyModifications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "modificationType": {"type": "string"},
                                "modificationDate": {
                                    "type": "string",
                                    "format": "date",
                                },
                                "modificationDetails": {"type": "string"},
                            },
                            "required": [
                                "modificationType",
                                "modificationDate",
                                "modificationDetails",
                            ],
                        },
                    },
                    "company": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "capital": {"type": "number"},
                            "registryDetails": {"type": "string"},
                            "MainbusinessPurpose": {
                                "type": "string",
                                "description": "Summary of the business purpose of the company in less than 10 words",
                            },
                        },
                        "required": ["name", "RUT", "capital", "registryDetails"],
                    },
                    "parties": {  # TODO: Unify JSON schema for incorporation, modification, dissolutionn
                        "type": "array",
                        "description": "The persons or companies that are modifying an existing company",
                        "items": {
                            "type": "object",
                            "properties": {
                                "EntityType": {
                                    "type": "string",
                                    "enum": ["Individual", "ExistingCompany"],
                                    "description": "Type of the party, can be a person or a company",
                                },
                                "name": {"type": "string"},
                                "RUN": {
                                    "type": "string",
                                    "description": "the RUN, RUT, CI or tax ID of the person or existing company",
                                },
                                "property_of_company": {
                                    "type": "string",
                                    "description": "Number of stocks or percentage of capital owned by person or company",
                                },
                                "address": {
                                    "type": "string",
                                    "description": "the address of the person or existing company",
                                },
                                "represented_by": {
                                    "type": "string",
                                    "description": "if the party is an existing company, name of the representative",
                                },
                            },
                            "required": ["name", "RUN", "address"],
                        },
                    },
                },
                "required": ["companyModifications", "company", "parties"],
            },
        },
    ]
    response = _openai_api_caller(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call={
            "name": "get_modification_entities"
        },  # force to call specific function
    )

    response_message = {}

    response_message = response["choices"][0]["message"]["function_call"]["arguments"]

    return response_message


def function_disolucion(pdf_text):
    messages = [{"role": "user", "content": pdf_text}]
    functions = [
        {
            "name": "get_dissolution_entities",
            "description": "Identify the main entities, participants and events in a company dissolution legal text",
            "parameters": {
                "title": "Legal Document",
                "type": "object",
                "properties": {
                    "parties": {
                        "type": "array",
                        "description": "The persons or companies that are ending a company",
                        "items": {
                            "type": "object",
                            "properties": {
                                "party_type": {
                                    "type": "string",
                                    "enum": ["person", "company"],
                                    "description": "Type of the party, can be a person or a company",
                                },
                                "name": {"type": "string"},
                                "RUN": {
                                    "type": "string",
                                    "description": "the RUN, RUT, CI or tax ID of the person or existing company",
                                },
                                "property_of_company": {
                                    "type": "string",
                                    "description": "Number of stocks or percentage of capital owned by person or company",
                                },
                                "address": {
                                    "type": "string",
                                    "description": "the address of the person or existing company",
                                },
                                "represented_by": {
                                    "type": "string",
                                    "description": "if the party is an existing company, name of the representative",
                                },
                            },
                            "required": ["name", "RUN", "address"],
                        },
                    },
                    "company": {
                        "type": "object",
                        "properties": {
                            "registryDetails": {"type": "string"},
                            "endBalanceDate": {
                                "type": "string",
                                "description": "the date of the end balance of the company",
                            },
                        },
                        "required": ["name", "RUT", "registryDetails"],
                    },
                    "dissolutionDetails": {
                        "type": "object",
                        "properties": {
                            "dissolutionDate": {
                                "type": "string",
                                "description": "the date of the dissolution of the company",
                            },
                            "liquidationProcedure": {
                                "type": "string",
                                "description": "details on how the liquidation of the company will be handled",
                            },
                            "capitalDetails": {
                                "type": "string",
                                "description": "details about the capital of the company at the time of dissolution",
                            },
                        },
                        "required": ["dissolutionDate"],
                    },
                },
                "required": ["parties", "company", "dissolutionDetails"],
            },
        }
    ]
    response = _openai_api_caller(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call={
            "name": "get_dissolution_entities"
        },  # force to call specific function
    )

    response_message = {}

    response_message = response["choices"][0]["message"]["function_call"]["arguments"]

    return response_message
