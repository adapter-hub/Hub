### Definitions

- `<model_name>`: The shortcut or identifier name of a pre-trained model available from Huggingface (e.g. `bert-base-uncased`, `roberta-large`).
- `<config_id>`: 16-char hash of the adapter architecture.
- `<config>`: an identifier for an adapter architecture (e.g. `pfeiffer`).
- `<task>`: the name of the task the adapter is categorized under (e.g. `sentiment`, `question_answering`, `nli` for task adapters or `en`, `de` for language adapters).
- `<subtask>`: the dataset or domain the adapter was trained on (e.g. `multinli`, `squad1.1`, `wiki`)
- `<weights_name>` (of an adapter): the name under which adapter weights are saved in the weights file. Given in the `name` attribute of the adapter config and required for reloading. (This name originates from calling `model.add_adapter(<weights_name>, <type>)`).
- `<type>`: the adapter type (e.g. `text_task`).
- `<org_name>`: name of the orga., GH user... that maintains the adapter.

### Loading

Adapters are loaded with: `model.load_adapter(<specifier>, <type>, config=<config>, model=<model_name>, version=<version>)`.

`<specifier>` can be one of the following iff globally unique:
- `<task>`
- `<task>/<subtask>`
- `<subtask>`
- `<task>@<org_name>`
- `<task>/<subtask>@<org_name>`
- `<subtask>@<org_name>`

### File structure

#### Index files

Placed in `/dist/index_<type>/<model_name>.json`.

```
{
    <task>: {
        <subtask>: {
            "default": "<org_name>/<file_name>.json",
            <config_id>: {
                "default": "<org_name>/<file_name>.json",
                "versions": {
                    <org_name>: "<org_name>/<file_name>.json"
                    ...
                }
            }
            ...
        }
        ...
    }
    ...
}
```

#### Config files

Placed in `/adapters/<org_name>/<file_name>.yaml`.

Schema defined in `/scripts/schemas/adapter.schema.json`.
