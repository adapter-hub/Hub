import json
import os
from utils import SCHEMA_FOLDER, TEMPLATE_FOLDER


def cmt(s):
    return f"# {s}"


def _keyfunc(required):
    return lambda kv: "000"+str(required.index(kv[0])) if kv[0] in required else kv[0]


def generate_item(name, schema, lines, required=[], indent=0):
    if '$comment' in schema and schema['$comment'] == '$hidden':
        return
    if 'description' in schema:
        lines.append(" "*indent+cmt(schema['description']))
    if 'examples' in schema:
        lines.append(" "*indent+cmt(f"Example: {schema['examples'][0]}"))
    if schema['type'] == 'object' and 'properties' in schema:
        if name:
            if name in required:
                comment = " # TODO: REQUIRED"
            else:
                comment = ""
            lines.append(" "*indent+f"{name}:"+comment)
        for name, data in sorted(schema['properties'].items(), key=_keyfunc(schema.get('required', []))):
            generate_item(
                name, data, lines,
                required=schema.get('required', []),
                indent=indent+2
            )
    elif schema['type'] == 'array':
        if name:
            if name in required:
                comment = " # TODO: REQUIRED"
            else:
                comment = ""
            lines.append(" "*indent+f"{name}:"+comment)
        first_i = len(lines)
        generate_item(None, schema['items'], lines, indent=indent+2)
        list_prefix = " "*(indent+2)+"- "
        lines[first_i] =list_prefix+lines[first_i].strip()
        lines.append(cmt(list_prefix+"..."))
    else:
        if name in required and indent==0:
            lines.append(" "*indent+f"{name}: \"TODO: REQUIRED\"")
        elif name:
            lines.append(" "*indent+f"{name}: \"\"")
        else:
            lines.append(" "*indent+"\"\"")
    if indent == 0:
        lines.append("")


def generate_templates():
    for item in os.listdir(SCHEMA_FOLDER):
        if not os.path.isfile(os.path.join(SCHEMA_FOLDER, item)):
            continue
        with open(os.path.join(SCHEMA_FOLDER, item), 'r') as f:
            schema = json.load(f)
        # generate yaml template
        print("Generating template for '{}'...".format(item))
        lines = []
        lines.append(cmt(schema['title']))
        lines.append(cmt(schema['description']))
        lines.append(cmt("-"*20))
        lines.append("")
        for name, data in sorted(schema['properties'].items(), key=_keyfunc(schema['required'])):
            generate_item(name, data, lines, required=schema['required'])
        file_name = item.split(".")[0]
        out_file = os.path.join(TEMPLATE_FOLDER, f"{file_name}.template.yaml")
        with open(out_file, 'x') as f:
            f.write('\n'.join(lines))


def delete_existing_files(suffix=".template.yaml"):
    for item in os.listdir(TEMPLATE_FOLDER):
        if item.endswith(suffix):
            os.remove(os.path.join(TEMPLATE_FOLDER, item))


if __name__ == "__main__":
    if os.path.exists(TEMPLATE_FOLDER):
        delete_existing_files()
    else:
        os.makedirs(TEMPLATE_FOLDER)
    generate_templates()
