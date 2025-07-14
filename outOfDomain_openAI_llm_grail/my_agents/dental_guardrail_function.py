from agents import GuardrailFunctionOutput, Runner
from .dental_guardrail_agent import dental_guardrail_agent

async def run_dental_guardrail_check(input_data: str) -> GuardrailFunctionOutput:
    # รัน Agent ที่ใช้ LLM ตรวจสอบ
    result = await Runner.run(dental_guardrail_agent, input_data)

    # แปลงผลลัพธ์ให้อยู่ใน schema ที่ประกาศ
    final_output = result.final_output_as(dental_guardrail_agent.output_type)

    # ถ้าไม่อยู่ใน scope => Tripwire (block)
    tripwire = not final_output.is_in_scope

    return GuardrailFunctionOutput(
        output_info={
            "reasoning": final_output.reasoning
        },
        tripwire_triggered=tripwire
    )
