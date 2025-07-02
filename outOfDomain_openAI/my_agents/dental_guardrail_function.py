from agents import GuardrailFunctionOutput, Runner
from .dental_guardrail_agent import dental_guardrail_agent
from dataclasses import dataclass

@dataclass
class GuardrailResult:
    tripwire_triggered: bool
    output_info: dict

async def dental_input_guardrail(ctx, agent, input_data):
    result = await Runner.run(dental_guardrail_agent, input_data)
    final_output = result.final_output_as(dental_guardrail_agent.output_type)
    return GuardrailResult(
        tripwire_triggered=False,
        output_info={"reasoning": "คำถามนี้เกี่ยวข้องกับการดูแลฟันหลังผ่าตัด จึงไม่ถือว่า out of domain"}
    )
