#!/usr/bin/env python3
"""
MCP Setup Script for Systems Performance Analysis

Configura Context7 MCP server e gera documentação das bibliotecas.
Seguindo padrões de context engineering.
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPSetup:
    """Configuração do MCP Context7 para documentação de bibliotecas."""

    def __init__(self, docs_dir: Optional[Path] = None):
        """
        Inicializa o setup MCP.

        Args:
            docs_dir: Diretório para documentação gerada
        """
        self.docs_dir = docs_dir or Path(__file__).parent.parent / "docs" / "libs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)

        # Bibliotecas para documentar
        self.libraries = {
            "psutil": {
                "url": "https://psutil.readthedocs.io/en/latest/",
                "description": "System and process utilities library",
                "functions": [
                    "cpu_percent",
                    "virtual_memory",
                    "disk_usage",
                    "net_io_counters",
                    "getloadavg",
                ],
            },
            "matplotlib": {
                "url": "https://matplotlib.org/stable/contents.html",
                "description": "Plotting and visualization library",
                "functions": [
                    "pyplot",
                    "figure",
                    "savefig",
                    "subplots",
                    "bar",
                    "plot",
                    "hist",
                    "axvline",
                ],
            },
            "pandas": {
                "url": "https://pandas.pydata.org/docs/",
                "description": "Data manipulation and analysis library",
                "functions": [
                    "DataFrame",
                    "Series",
                    "read_csv",
                    "to_datetime",
                    "groupby",
                    "merge",
                    "concat",
                ],
            },
            "numpy": {
                "url": "https://numpy.org/doc/stable/",
                "description": "Numerical computing library",
                "functions": [
                    "array",
                    "mean",
                    "median",
                    "std",
                    "percentile",
                    "histogram",
                    "random",
                    "linspace",
                ],
            },
            "schedule": {
                "url": "https://schedule.readthedocs.io/en/stable/",
                "description": "Job scheduling library",
                "functions": ["every", "run_pending", "cancel_job"],
            },
            "jinja2": {
                "url": "https://jinja.palletsprojects.com/",
                "description": "Template engine for Python",
                "functions": ["Template", "Environment", "FileSystemLoader"],
            },
            "rich": {
                "url": "https://rich.readthedocs.io/",
                "description": "Rich text and beautiful formatting",
                "functions": ["Console", "Progress", "Table", "Panel"],
            },
        }

    def setup_context7_mcp(self) -> bool:
        """
        Configura o MCP server Context7.

        Returns:
            True se sucesso, False caso contrário
        """
        logger.info("Setting up Context7 MCP server...")

        try:
            # Adicionar MCP server
            cmd = [
                "claude",
                "mcp",
                "add",
                "--transport",
                "http",
                "context7",
                "https://mcp.context7.com/mcp",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Context7 MCP server added successfully")
                logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"❌ Failed to add Context7 MCP: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.error("❌ Claude CLI not found. Please install Claude Code first.")
            return False
        except Exception as e:
            logger.error(f"❌ Error setting up Context7 MCP: {e}")
            return False

    def fetch_library_docs(
        self, library_name: str, library_info: Dict
    ) -> Optional[str]:
        """
        Busca documentação de uma biblioteca específica.

        Args:
            library_name: Nome da biblioteca
            library_info: Informações da biblioteca

        Returns:
            Documentação em formato Markdown ou None se falhar
        """
        logger.info(f"Fetching documentation for {library_name}...")

        try:
            # Tentar buscar documentação via web scraping
            # Em um cenário real, usaríamos Context7 MCP aqui
            # Por ora, vamos gerar documentação básica

            docs_content = self._generate_library_docs(library_name, library_info)

            if docs_content:
                logger.info(f"✅ Documentation generated for {library_name}")
                return docs_content
            else:
                logger.warning(f"⚠️ No documentation generated for {library_name}")
                return None

        except Exception as e:
            logger.error(f"❌ Error fetching docs for {library_name}: {e}")
            return None

    def _generate_library_docs(self, library_name: str, library_info: Dict) -> str:
        """
        Gera documentação básica da biblioteca.

        Args:
            library_name: Nome da biblioteca
            library_info: Informações da biblioteca

        Returns:
            Documentação em formato Markdown
        """
        docs = []

        # Header
        docs.append(f"# {library_name.title()} Documentation")
        docs.append("")
        docs.append(f"**Description**: {library_info['description']}")
        docs.append(f"**URL**: {library_info['url']}")
        docs.append("")

        # Key Functions
        if library_info.get("functions"):
            docs.append("## Key Functions")
            docs.append("")

            for func in library_info["functions"]:
                docs.append(f"### `{func}`")
                docs.append("")
                docs.append(f"```python")
                docs.append(f"import {library_name}")
                docs.append(f"# Usage example for {func}")
                docs.append(f"result = {library_name}.{func}()")
                docs.append(f"```")
                docs.append("")

        # Common Patterns
        docs.append("## Common Patterns in Systems Performance Analysis")
        docs.append("")

        if library_name == "psutil":
            docs.append("""
### CPU Monitoring
```python
import psutil

# CPU utilization
cpu_percent = psutil.cpu_percent(interval=1)

# Load averages (Linux/Unix)
load_avg = psutil.getloadavg()
```

### Memory Monitoring
```python
# Virtual memory
memory = psutil.virtual_memory()
print(f"Memory usage: {memory.percent}%")

# Swap memory
swap = psutil.swap_memory()
print(f"Swap usage: {swap.percent}%")
```

### Disk I/O
```python
# Disk usage
disk_usage = psutil.disk_usage('/')
print(f"Disk usage: {disk_usage.percent}%")

# Disk I/O counters
disk_io = psutil.disk_io_counters()
print(f"Read bytes: {disk_io.read_bytes}")
```
""")

        elif library_name == "matplotlib":
            docs.append("""
### Performance Charts
```python
import matplotlib.pyplot as plt

# Bar chart for USE scores
components = ['CPU', 'Memory', 'Disk', 'Network']
scores = [75, 60, 45, 30]

plt.bar(components, scores)
plt.ylabel('Score (%)')
plt.title('USE Method Scores')
plt.show()
```

### Latency Histogram
```python
import numpy as np

latency_data = np.random.lognormal(2, 0.5, 1000)

plt.hist(latency_data, bins=50, alpha=0.7)
plt.xlabel('Latency (ms)')
plt.ylabel('Frequency')
plt.title('Latency Distribution')
plt.show()
```
""")

        elif library_name == "pandas":
            docs.append("""
### Performance Data Analysis
```python
import pandas as pd

# Create DataFrame from metrics
data = {
    'component': ['CPU', 'Memory', 'Disk'],
    'utilization': [75.5, 60.2, 45.8],
    'saturation': [15.3, 8.1, 22.4]
}

df = pd.DataFrame(data)
print(df.describe())

# Filter high utilization components
high_usage = df[df['utilization'] > 70]
print(high_usage)
```
""")

        # Performance Tips
        docs.append("## Performance Tips")
        docs.append("")

        if library_name == "psutil":
            docs.append("""
- Use `interval=1` for accurate CPU measurements
- Cache metrics to avoid excessive system calls
- Handle `AccessDenied` exceptions gracefully
- Use `/proc` filesystem directly for Linux-specific metrics
""")
        elif library_name == "matplotlib":
            docs.append("""
- Use `plt.style.use('seaborn')` for professional charts
- Save figures with `dpi=150` for quality
- Use `bbox_inches='tight'` to prevent label cutoff
- Close figures with `plt.close()` to prevent memory leaks
""")
        elif library_name == "pandas":
            docs.append("""
- Use vectorized operations instead of loops
- Avoid `iterrows()` for large datasets
- Use `category` dtype for low-cardinality strings
- Consider `chunksize` for large file processing
""")

        # Integration Examples
        docs.append("## Integration with Systems Performance Analysis")
        docs.append("")
        docs.append(f"""
This library is used in the Systems Performance Analysis Tool for:

- **Data Collection**: Gathering system metrics
- **Data Processing**: Analyzing performance data
- **Visualization**: Creating performance charts
- **Reporting**: Generating analysis reports

For specific usage examples, see the main source code in `src/`.
""")

        # References
        docs.append("## References")
        docs.append("")
        docs.append(f"- [Official Documentation]({library_info['url']})")
        docs.append(
            f"- [GitHub Repository](https://github.com/{library_name}/{library_name})"
        )
        docs.append("- [Systems Performance Analysis Tool](../README.md)")

        return "\n".join(docs)

    def save_library_docs(self, library_name: str, content: str) -> bool:
        """
        Salva documentação da biblioteca em arquivo MD.

        Args:
            library_name: Nome da biblioteca
            content: Conteúdo da documentação

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            filename = self.docs_dir / f"{library_name.upper()}.md"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"✅ Documentation saved to {filename}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving docs for {library_name}: {e}")
            return False

    def generate_all_docs(self) -> bool:
        """
        Gera documentação para todas as bibliotecas.

        Returns:
            True se sucesso geral, False caso contrário
        """
        logger.info("Generating documentation for all libraries...")

        success_count = 0
        total_count = len(self.libraries)

        for library_name, library_info in self.libraries.items():
            try:
                content = self.fetch_library_docs(library_name, library_info)

                if content and self.save_library_docs(library_name, content):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Failed to generate docs for {library_name}")

            except Exception as e:
                logger.error(f"❌ Error processing {library_name}: {e}")

        logger.info(
            f"Documentation generation complete: {success_count}/{total_count} libraries"
        )
        return success_count == total_count

    def create_index(self) -> bool:
        """
        Cria arquivo index.md para documentação das bibliotecas.

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            index_content = []
            index_content.append("# Library Documentation Index")
            index_content.append("")
            index_content.append(
                "This directory contains documentation for libraries used in the Systems Performance Analysis Tool."
            )
            index_content.append("")
            index_content.append("## Available Libraries")
            index_content.append("")

            for library_name, library_info in self.libraries.items():
                filename = f"{library_name.upper()}.md"
                index_content.append(
                    f"- [{library_name.title()}]({filename}) - {library_info['description']}"
                )

            index_content.append("")
            index_content.append("## Usage")
            index_content.append("")
            index_content.append(
                "These documentation files are generated automatically and used for context engineering with AI assistants."
            )
            index_content.append("")
            index_content.append("To regenerate documentation:")
            index_content.append("```bash")
            index_content.append("python scripts/setup-mcp.py")
            index_content.append("```")

            index_path = self.docs_dir / "index.md"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("\n".join(index_content))

            logger.info(f"✅ Index created at {index_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error creating index: {e}")
            return False

    def run_full_setup(self) -> bool:
        """
        Executa setup completo do MCP e documentação.

        Returns:
            True se sucesso geral, False caso contrário
        """
        logger.info("🚀 Starting full MCP setup...")

        # Step 1: Configurar Context7 MCP
        mcp_success = self.setup_context7_mcp()

        # Step 2: Gerar documentação das bibliotecas
        docs_success = self.generate_all_docs()

        # Step 3: Criar índice
        index_success = self.create_index()

        overall_success = mcp_success and docs_success and index_success

        if overall_success:
            logger.info("🎉 MCP setup completed successfully!")
            logger.info(f"📚 Documentation available in: {self.docs_dir}")
        else:
            logger.error("❌ MCP setup completed with errors")

        return overall_success


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP Setup for Systems Performance Analysis"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        help="Directory for generated documentation (default: docs/libs)",
    )
    parser.add_argument(
        "--mcp-only",
        action="store_true",
        help="Only setup MCP server, skip documentation generation",
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Only generate documentation, skip MCP setup",
    )

    args = parser.parse_args()

    # Inicializar setup
    setup = MCPSetup(args.docs_dir)

    try:
        if args.mcp_only:
            success = setup.setup_context7_mcp()
        elif args.docs_only:
            success = setup.generate_all_docs() and setup.create_index()
        else:
            success = setup.run_full_setup()

        if success:
            print("\n✅ Setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup completed with errors!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
