import re
import logging
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from app.llm.provider import LLMProvider
from app.llm.schemas import (
    IntentClassificationResult, IntentEnum, ExtractedEntities,
    CopilotResponse, Source, AffectedProduct, RecommendedAction
)

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class FakeLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM Provider for 100% offline, fast automated testing.
    Requires no external API keys or background Ollama daemon.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "Deterministic FakeLLM synthesis based on trusted application context."

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None
    ) -> T:
        # Extract user question from prompt if formatted with template
        q_match = re.search(r'USER QUESTION:\s*[\r\n\s]*"(.*?)"', prompt, re.DOTALL | re.IGNORECASE)
        q_text = q_match.group(1) if q_match else prompt
        p_lower = q_text.lower()


        # 1. Handle Intent Classification
        if response_schema == IntentClassificationResult:
            intent = IntentEnum.UNKNOWN
            entities = ExtractedEntities()

            # SKU Extraction (e.g. SKU-001, SKU-102)
            sku_match = re.search(r"sku[-_]?(\d+)", p_lower)
            if sku_match:
                entities.sku = f"SKU-{int(sku_match.group(1)):03d}"

            # Supplier Extraction (e.g. SUP-001, GlobalTech, ABC Industrial)
            if "sup-001" in p_lower or "abc" in p_lower:
                entities.supplier = "ABC Industrial"
            elif "sup-002" in p_lower or "xyz" in p_lower:
                entities.supplier = "XYZ Electronics"
            elif "sup-003" in p_lower or "globaltech" in p_lower:
                entities.supplier = "GlobalTech Components"

            # Time Horizon Extraction (e.g. 14 days, 30 days)
            days_match = re.search(r"(\d+)\s*days?", p_lower)
            if days_match:
                entities.horizon_days = int(days_match.group(1))

            # Intent Category Order (Specific to General)
            if any(k in p_lower for k in ["contract", "penalty", "agreement"]):
                intent = IntentEnum.CONTRACT_QUESTION
            elif any(k in p_lower for k in ["policy", "guideline", "emergency procurement"]):
                intent = IntentEnum.POLICY_QUESTION
            elif any(k in p_lower for k in ["supplier", "performance", "on-time", "lead time"]):
                intent = IntentEnum.SUPPLIER_INFORMATION
            elif any(k in p_lower for k in ["forecast", "demand", "predict"]):
                intent = IntentEnum.FORECAST
            elif any(k in p_lower for k in ["stockout", "risk", "shortage", "inventory"]):
                intent = IntentEnum.INVENTORY_RISK
            else:
                intent = IntentEnum.GENERAL_SUPPLY_CHAIN

            return IntentClassificationResult(
                intent=intent,
                confidence=0.95,
                entities=entities,
                reasoning="Deterministic fake intent classification based on user question keywords."
            )


        # 2. Handle Copilot Response Generation
        if response_schema == CopilotResponse:
            # Extract cited sources present in prompt markdown
            sources = []
            doc_matches = re.findall(r"\[Document:\s*(.+?)\]", prompt)
            for doc in set(doc_matches):
                sources.append(Source(
                    document_name=doc.strip(),
                    document_type="Document",
                    section="Relevant Terms",
                    similarity=0.85
                ))

            if not sources:
                sources.append(Source(
                    document_name="knowledge_base/procurement_policies/procurement_policy.md",
                    document_type="Procurement Policy",
                    section="General Terms",
                    similarity=0.90
                ))

            # Parse risk level or metrics from prompt context if present
            risk_lvl = "MEDIUM"
            if "critical" in p_lower:
                risk_lvl = "CRITICAL"
            elif "high" in p_lower:
                risk_lvl = "HIGH"
            elif "low" in p_lower:
                risk_lvl = "LOW"

            affected = [
                AffectedProduct(
                    sku="SKU-001",
                    product_name="Microcontroller Unit",
                    reason="Inventory level below reorder point with upcoming forecast demand."
                )
            ]

            actions = [
                RecommendedAction(
                    action="REORDER",
                    priority="HIGH",
                    reason="Replenish stock to meet 14-day forecasted lead-time demand."
                )
            ]

            return CopilotResponse(
                summary="Grounded supply-chain analysis produced from trusted application context.",
                intent="INVENTORY_RISK" if "risk" in p_lower else "POLICY_QUESTION",
                answer="Based on trusted system metrics and retrieved policy documentation, inventory levels and supplier lead-time parameters have been evaluated. All numerical figures are derived from the deterministic decision engine.",
                risk_level=risk_lvl,
                affected_products=affected,
                recommended_actions=actions,
                explanation="The deterministic risk engine calculated a stockout probability based on historical sales variance and supplier delivery lead times.",
                confidence=0.92,
                sources=sources,
                data_used=["PostgreSQL Database", "ML Forecast Model", "Risk Engine", "RAG Knowledge Base"],
                warnings=["This recommendation is for decision support; purchase order execution requires user confirmation."]
            )

        # 3. Handle SQL Query Generation (Phase 7)
        if response_schema.__name__ == "SQLQuery":
            if "drop table" in p_lower or "malicious" in p_lower:
                from app.sql.schemas import SQLQuery
                return SQLQuery(
                    sql="DROP TABLE suppliers;",
                    explanation="Simulated malicious LLM generated SQL for security testing."
                )

            if "on-time" in p_lower or "85" in p_lower or "below" in p_lower:
                sql_str = "SELECT s.supplier_code, s.name, s.reliability_score FROM suppliers s WHERE s.reliability_score < 85.0 LIMIT 50"
            elif "delayed" in p_lower or "purchase order" in p_lower:
                sql_str = "SELECT po.po_number, s.name, po.status FROM purchase_orders po JOIN suppliers s ON po.supplier_id = s.id WHERE po.status = 'DELAYED' LIMIT 50"
            elif "sales" in p_lower or "top" in p_lower:
                sql_str = "SELECT p.sku, p.name, SUM(s.quantity) AS total_qty FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.id, p.sku, p.name ORDER BY total_qty DESC LIMIT 10"
            elif "lead time" in p_lower:
                sql_str = "SELECT s.name, AVG(s.average_lead_time_days) AS avg_lt FROM suppliers s GROUP BY s.id, s.name LIMIT 50"
            else:
                sql_str = "SELECT * FROM suppliers LIMIT 50"

            from app.sql.schemas import SQLQuery
            return SQLQuery(
                sql=sql_str,
                explanation="Deterministic fake SQL query generated for natural-language request."
            )

        # 4. Handle Planner Output Generation (Phase 8 Agent)
        if response_schema.__name__ == "PlannerOutput":
            from app.agents.schemas import PlannerOutput, ToolEnum
            intent = IntentEnum.GENERAL_SUPPLY_CHAIN
            entities = ExtractedEntities()
            tools = []

            # SKU Extraction (e.g. SKU-102, SKU-001)
            sku_match = re.search(r"sku[-_]?(\d+)", p_lower)
            if sku_match:
                prod_num = int(sku_match.group(1))
                entities.product_id = prod_num
                entities.sku = f"SKU-{prod_num:03d}"

            if "drop table" in p_lower or "malicious" in p_lower:
                tools = [ToolEnum.SQL]
                intent = IntentEnum.SUPPLIER_INFORMATION
            elif "what if" in p_lower or "what happens if" in p_lower or "simulate" in p_lower:
                tools = [ToolEnum.SIMULATION]
                intent = IntentEnum.INVENTORY_RISK
            elif "contract" in p_lower and "delayed" in p_lower:
                tools = [ToolEnum.SQL, ToolEnum.RAG, ToolEnum.RISK]
                intent = IntentEnum.CONTRACT_QUESTION
            elif "contract" in p_lower or "late deliver" in p_lower:
                tools = [ToolEnum.RAG]
                intent = IntentEnum.CONTRACT_QUESTION
            elif "why" in p_lower and "risk" in p_lower:
                tools = [ToolEnum.RISK, ToolEnum.FORECAST]
                intent = IntentEnum.INVENTORY_RISK
            elif "risk" in p_lower or "stockout" in p_lower:
                tools = [ToolEnum.RISK]
                intent = IntentEnum.INVENTORY_RISK
            elif "forecast" in p_lower or "demand" in p_lower:
                tools = [ToolEnum.FORECAST]
                intent = IntentEnum.FORECAST
            elif "supplier" in p_lower or "on-time" in p_lower or "85" in p_lower or "below" in p_lower:
                tools = [ToolEnum.SQL]
                intent = IntentEnum.SUPPLIER_INFORMATION
            else:
                tools = [ToolEnum.SQL, ToolEnum.RAG]

            return PlannerOutput(
                intent=intent,
                entities=entities,
                tools=tools,
                reason="Deterministic fake planner selection based on question keywords."
            )

        # 5. Handle Simulation Scenario Parsing
        if response_schema.__name__ == "SimulationScenario":
            from app.simulation.scenarios import _heuristic_parse_scenario
            return _heuristic_parse_scenario(q_text)

        # 6. Fallback for generic schemas
        try:
            return response_schema()
        except Exception:
            raise ValueError(f"FakeLLMProvider cannot construct default instance for schema {response_schema}")


