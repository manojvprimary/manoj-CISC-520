import os
import json
import subprocess
import tempfile
import sys
import math
import pandas as pd
import requests

from config import (
    SAC_CSV_PATH,
    NYC_SHELTER_URL,
    DATASETS,
    PLOT_PREAMBLE,
    PLOT_POSTAMBLE,
)

_dataset_cache = {}


def clean_value(v):
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v


def clean_dataframe(df):
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(clean_value)
    return df


def load_sac_csv(path):
    df = pd.read_csv(path, header=[0, 1], encoding="utf-8-sig")
    top_labels = []
    current = ""
    for col in df.columns:
        top = col[0].strip()
        if not top.startswith("Unnamed"):
            current = top
        top_labels.append(current)
    new_cols = []
    for (_, bottom), top in zip(df.columns, top_labels):
        bottom = bottom.strip()
        if top in ("Dog", "Cat"):
            new_cols.append(f"{top}_{bottom}")
        else:
            new_cols.append(bottom)
    df.columns = new_cols
    for col in df.columns:
        if col not in ("State", "Year"):
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .apply(pd.to_numeric, errors="coerce")
            )
    return df


def execute_python(code, context_vars=None):
    full_code = PLOT_PREAMBLE
    if context_vars:
        full_code += context_vars + "\n"
    full_code += code + "\n"
    full_code += PLOT_POSTAMBLE

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(full_code)
        fname = f.name

    try:
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        plots = []
        clean_stdout = stdout
        if "__PLOTS__" in stdout:
            parts = stdout.split("__PLOTS__", 1)
            clean_stdout = parts[0].strip()
            try:
                plots = json.loads(parts[1].strip())
            except Exception:
                pass

        return {
            "success": result.returncode == 0,
            "stdout": clean_stdout,
            "stderr": stderr,
            "plots": plots,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Code execution timed out after 30 seconds",
            "plots": [],
        }
    finally:
        try:
            os.unlink(fname)
        except Exception:
            pass


def analyze_dataset(dataset_name, instruction):
    try:
        if dataset_name not in DATASETS:
            return {"error": f"Unknown dataset. Available: {list(DATASETS.keys())}"}

        if dataset_name in _dataset_cache:
            result = dict(_dataset_cache[dataset_name])
            result["instruction"] = instruction
            return result

        if dataset_name == "sac_national":
            if not os.path.exists(SAC_CSV_PATH):
                return {"error": f"SAC CSV not found at {SAC_CSV_PATH}"}
            df = load_sac_csv(SAC_CSV_PATH)
            df = clean_dataframe(df)
            result = {
                "dataset": dataset_name,
                "csv_path": SAC_CSV_PATH,
                "rows": int(len(df)),
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample": df.head(5).values.tolist(),
                "note": "Columns are prefixed Dog_ or Cat_ for the respective species. State and Year identify each row.",
            }
            _dataset_cache[dataset_name] = result
            result = dict(result)
            result["instruction"] = instruction
            return result

        import kagglehub

        path = kagglehub.dataset_download(DATASETS[dataset_name])
        df = None
        csv_path = None
        for file in os.listdir(path):
            if file.endswith(".csv"):
                csv_path = os.path.join(path, file)
                df = pd.read_csv(csv_path)
                break

        if df is None:
            return {"error": "No CSV found in dataset"}

        df = clean_dataframe(df)
        result = {
            "dataset": dataset_name,
            "csv_path": csv_path,
            "rows": int(len(df)),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample": df.head(5).values.tolist(),
        }
        _dataset_cache[dataset_name] = result
        result = dict(result)
        result["instruction"] = instruction
        return result
    except Exception as e:
        return {"error": str(e)}


def fetch_nyc_shelter_data(limit=500):
    try:
        limit = min(int(limit), 1000)
        resp = requests.get(NYC_SHELTER_URL, params={"$limit": limit}, timeout=15)
        resp.raise_for_status()
        records = resp.json()
        if not records:
            return {"error": "No records returned from NYC API"}
        columns = list(records[0].keys())
        return {
            "source": "NYC Animal Care & Control (live API)",
            "url": NYC_SHELTER_URL,
            "records_fetched": len(records),
            "columns": columns,
            "sample": records[:5],
            "all_records_json": json.dumps(records),
        }
    except requests.exceptions.Timeout:
        return {"error": "NYC API request timed out"}
    except Exception as e:
        return {"error": str(e)}


def build_csv_context(csv_context):
    if not csv_context:
        return "", ""
    try:
        cols = list(pd.read_csv(csv_context, nrows=0).columns)
    except Exception:
        cols = []
    col_str = ", ".join(cols) if cols else "unknown"
    suffix = (
        f"\n\n[User has uploaded a CSV. It is loaded as `df` in execute_python. "
        f"Columns: {col_str}]"
    )
    code_ctx = f"import pandas as pd\ndf = pd.read_csv({repr(csv_context)})\n"
    return suffix, code_ctx


def execute_tool(tool_name, tool_input, csv_code_context, all_plots):
    is_error = False
    output = ""

    if tool_name == "execute_python":
        code = tool_input.get("code", "")
        exec_result = execute_python(code, context_vars=csv_code_context)
        if exec_result.get("plots"):
            all_plots.extend(exec_result["plots"])
        if exec_result["success"]:
            output = exec_result["stdout"] or "(code ran successfully, no printed output)"
        else:
            is_error = True
            output = f"Error:\n{exec_result['stderr']}\n\nStdout:\n{exec_result['stdout']}"

    elif tool_name == "analyze_dataset":
        dataset_name = tool_input.get("dataset_name", "austin_shelter")
        instruction = tool_input.get("instruction", "")
        result = analyze_dataset(dataset_name, instruction)
        if "error" in result:
            is_error = True
            output = result["error"]
        else:
            output = json.dumps(result)
            csv_path = result.get("csv_path")
            if csv_path:
                if dataset_name == "sac_national":
                    csv_code_context += (
                        "import pandas as pd\n"
                        f"_df_raw = pd.read_csv('{csv_path}', header=[0,1], encoding='utf-8-sig')\n"
                        "_top_labels = []\n"
                        "_cur = ''\n"
                        "for _col in _df_raw.columns:\n"
                        "    _t = _col[0].strip()\n"
                        "    if not _t.startswith('Unnamed'): _cur = _t\n"
                        "    _top_labels.append(_cur)\n"
                        "_new_cols = []\n"
                        "for (_ignored, _bot), _top in zip(_df_raw.columns, _top_labels):\n"
                        "    _bot = _bot.strip()\n"
                        "    _new_cols.append(f'{_top}_{_bot}' if _top in ('Dog', 'Cat') else _bot)\n"
                        "_df_raw.columns = _new_cols\n"
                        "for _c in _df_raw.columns:\n"
                        "    if _c not in ('State', 'Year'):\n"
                        "        _df_raw[_c] = _df_raw[_c].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce')\n"
                        "df = _df_raw\n"
                    )
                else:
                    csv_code_context += (
                        f"import pandas as pd\ndf = pd.read_csv('{csv_path}')\n"
                    )

    elif tool_name == "fetch_nyc_shelter_data":
        limit = tool_input.get("limit", 500)
        result = fetch_nyc_shelter_data(limit)
        if "error" in result:
            is_error = True
            output = result["error"]
        else:
            records_json = result.pop("all_records_json", "[]")
            output = json.dumps(result)
            csv_code_context += (
                "import pandas as pd, json\n"
                f"df = pd.DataFrame(json.loads({repr(records_json)}))\n"
                "for _c in df.columns:\n"
                "    df[_c] = pd.to_numeric(df[_c], errors='ignore')\n"
            )
    else:
        is_error = True
        output = f"Unknown tool: {tool_name}"

    return output, is_error, csv_code_context
