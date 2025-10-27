#!/usr/bin/env python3
"""
Local Time Series Database for Performance Metrics

Armazena histórico de métricas localmente usando SQLite + Pandas.
Alternativa leve ao Prometheus para histórico de longo prazo.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LocalTimeSeriesDB:
    """Banco de dados de séries temporais local."""

    def __init__(self, db_path: str = "performance_history.db"):
        """
        Inicializa banco de dados local.

        Args:
            db_path: Caminho para arquivo SQLite
        """
        self.db_path = Path(db_path)
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Inicializa tabelas do banco."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)

        # Tabela de métricas
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                source TEXT NOT NULL,
                component TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_unit TEXT,
                labels TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de análises
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                source TEXT NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL,
                utilization REAL,
                saturation REAL,
                errors REAL,
                recommendations TEXT,
                raw_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índices para performance
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_component ON metrics(component, metric_name)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_timestamp ON analyses(timestamp)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_component ON analyses(component)"
        )

        self.conn.commit()
        logger.info(f"Database initialized: {self.db_path}")

    def store_metrics(self, timestamp: datetime, source: str, metrics: Dict[str, Any]):
        """
        Armazena métricas no banco.

        Args:
            timestamp: Timestamp da coleta
            source: Fonte das métricas (ex: 'prometheus-remote')
            metrics: Dicionário com métricas
        """
        try:
            for component, data in metrics.items():
                if isinstance(data, dict):
                    for metric_name, value in data.items():
                        if isinstance(value, (int, float)):
                            self.conn.execute(
                                """
                                INSERT INTO metrics 
                                (timestamp, source, component, metric_name, metric_value, metric_unit)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    timestamp,
                                    source,
                                    component,
                                    metric_name,
                                    value,
                                    self._get_unit(metric_name),
                                ),
                            )

            self.conn.commit()
            logger.debug(f"Stored metrics from {source} at {timestamp}")

        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
            self.conn.rollback()

    def store_analysis(
        self, timestamp: datetime, source: str, analysis: Dict[str, Any]
    ):
        """
        Armazena análise USE no banco.

        Args:
            timestamp: Timestamp da análise
            source: Fonte da análise
            analysis: Resultados da análise
        """
        try:
            for component, data in analysis.items():
                if isinstance(data, dict) and "status" in data:
                    self.conn.execute(
                        """
                        INSERT INTO analyses 
                        (timestamp, source, component, status, score, utilization, saturation, 
                         errors, recommendations, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            timestamp,
                            source,
                            component,
                            data.get("status"),
                            data.get("score"),
                            data.get("utilization"),
                            data.get("saturation"),
                            data.get("errors"),
                            json.dumps(data.get("recommendations", [])),
                            json.dumps(data),
                        ),
                    )

            self.conn.commit()
            logger.debug(f"Stored analysis from {source} at {timestamp}")

        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")
            self.conn.rollback()

    def get_metrics_history(
        self,
        component: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Recupera histórico de métricas.

        Args:
            component: Componente (cpu, memory, disk, network)
            metric_name: Nome da métrica específica
            start_time: Data inicial
            end_time: Data final
            limit: Limite de registros

        Returns:
            DataFrame com histórico
        """
        query = "SELECT * FROM metrics WHERE component = ?"
        params = [component]

        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.sort_values("timestamp")
        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return pd.DataFrame()

    def get_analysis_history(
        self,
        component: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Recupera histórico de análises.

        Args:
            component: Componente específico
            start_time: Data inicial
            end_time: Data final
            limit: Limite de registros

        Returns:
            DataFrame com histórico
        """
        query = "SELECT * FROM analyses WHERE 1=1"
        params = []

        if component:
            query += " AND component = ?"
            params.append(component)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.sort_values("timestamp")
        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return pd.DataFrame()

    def get_trend_analysis(
        self, component: str, metric_name: str, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Analisa tendências de uma métrica.

        Args:
            component: Componente
            metric_name: Métrica
            hours: Horas para análise

        Returns:
            Análise de tendências
        """
        start_time = datetime.now() - timedelta(hours=hours)

        df = self.get_metrics_history(component, metric_name, start_time=start_time)

        if df.empty:
            return {"error": "No data available"}

        # Estatísticas básicas
        values = df["metric_value"]

        trend = {
            "component": component,
            "metric": metric_name,
            "period_hours": hours,
            "data_points": len(df),
            "current": values.iloc[-1] if len(values) > 0 else None,
            "min": values.min(),
            "max": values.max(),
            "avg": values.mean(),
            "std": values.std(),
            "trend": self._calculate_trend(values),
            "change_percent": self._calculate_change_percent(values),
            "unit": df["metric_unit"].iloc[0] if not df.empty else None,
        }

        return trend

    def _calculate_trend(self, values: pd.Series) -> str:
        """Calcula direção da tendência."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear regression
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

    def _calculate_change_percent(self, values: pd.Series) -> float:
        """Calcula percentual de mudança."""
        if len(values) < 2:
            return 0.0

        first = values.iloc[0]
        last = values.iloc[-1]

        if first == 0:
            return 0.0

        return ((last - first) / first) * 100

    def _get_unit(self, metric_name: str) -> str:
        """Determina unidade da métrica."""
        if "percent" in metric_name.lower() or "utilization" in metric_name.lower():
            return "%"
        elif "bytes" in metric_name.lower():
            return "bytes"
        elif "seconds" in metric_name.lower():
            return "seconds"
        elif "load" in metric_name.lower():
            return "load"
        else:
            return "unknown"

    def cleanup_old_data(self, days: int = 30):
        """Remove dados antigos."""
        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            # Remove métricas antigas
            self.conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_date,))

            # Remove análises antigas
            self.conn.execute(
                "DELETE FROM analyses WHERE timestamp < ?", (cutoff_date,)
            )

            self.conn.commit()
            logger.info(f"Cleaned up data older than {days} days")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

    def get_database_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco."""
        try:
            metrics_count = self.conn.execute(
                "SELECT COUNT(*) FROM metrics"
            ).fetchone()[0]

            analyses_count = self.conn.execute(
                "SELECT COUNT(*) FROM analyses"
            ).fetchone()[0]

            oldest_metric = self.conn.execute(
                "SELECT MIN(timestamp) FROM metrics"
            ).fetchone()[0]

            newest_metric = self.conn.execute(
                "SELECT MAX(timestamp) FROM metrics"
            ).fetchone()[0]

            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "metrics_count": metrics_count,
                "analyses_count": analyses_count,
                "date_range": {"oldest": oldest_metric, "newest": newest_metric},
                "database_size_bytes": db_size,
                "database_path": str(self.db_path),
            }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    def export_to_csv(self, output_dir: str = "exports"):
        """Exporta dados para CSV."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Export metrics
            metrics_df = pd.read_sql_query("SELECT * FROM metrics", self.conn)
            metrics_file = output_path / f"metrics_{timestamp}.csv"
            metrics_df.to_csv(metrics_file, index=False)

            # Export analyses
            analyses_df = pd.read_sql_query("SELECT * FROM analyses", self.conn)
            analyses_file = output_path / f"analyses_{timestamp}.csv"
            analyses_df.to_csv(analyses_file, index=False)

            logger.info(f"Data exported to {output_path}")
            return {
                "metrics_file": str(metrics_file),
                "analyses_file": str(analyses_file),
            }

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return {"error": str(e)}

    def close(self):
        """Fecha conexão com banco."""
        if self.conn:
            self.conn.close()


# Import numpy para trend analysis
import numpy as np
