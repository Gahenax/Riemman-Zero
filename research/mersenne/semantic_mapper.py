import ast
import json
import os
from pathlib import Path

def get_ast_features(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
        
    tree = ast.parse(source)
    
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    from_imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    
    return {
        "file": os.path.basename(filepath),
        "classes": classes,
        "functions": functions,
        "imports": imports + from_imports
    }

def build_knowledge_graph(target_dirs: list, out_file: str):
    print("==================================================")
    print(" GAHENAX SEMANTIC KNOWLEDGE ENGINE (AST MAPPER)")
    print("==================================================")
    
    graph = {"nodes": [], "edges": []}
    files_analyzed = 0
    
    for d in target_dirs:
        print(f"[SKE] Scanning Directory: {d}")
        for path in Path(d).rglob('*.py'):
            if 'venv' in path.parts or '__pycache__' in path.parts: continue
            
            try:
                features = get_ast_features(str(path))
                node_id = f"module_{features['file']}"
                
                graph["nodes"].append({
                    "id": node_id,
                    "label": features["file"],
                    "type": "python_module",
                    "metadata": features
                })
                
                # Create edges based on internal project imports
                for imp in features["imports"]:
                    if imp and ("src." in imp or "research." in imp or "tools." in imp):
                        graph["edges"].append({
                            "source": node_id,
                            "target": f"module_{imp.split('.')[-1]}.py",
                            "type": "imports"
                        })
                files_analyzed += 1
            except Exception as e:
                print(f"  [WARN] Could not parse {path.name}: {e}")
                
    print(f"[SKE] Analysis Complete. Parsed {files_analyzed} Python ASTs.")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=4)
        
    print(f"[SKE] Cognitive Topology Extracted to: {out_file}")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_path = os.path.join(base_dir, "artifacts", "architecture_map.json")
    
    dirs_to_scan = [
        os.path.join(base_dir, "research"),
        # We can add P-ATLAS dir here if needed, but scanning Mersenne for now
    ]
    
    build_knowledge_graph(dirs_to_scan, out_path)
