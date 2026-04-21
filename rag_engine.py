from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - handled at runtime
    Groq = None


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


@dataclass
class ReusablePrompt:
    system_prompt: str = (
        "You are an elite automotive consultant. Compare these two vehicles based on the "
        "provided technical specs. Provide a recommendation for a user living in Dubai."
    )
    user_template: str = (
        "Compare the following vehicles using only the provided spec context.\n\n"
        "Vehicle A:\n{car1}\n\n"
        "Vehicle B:\n{car2}\n\n"
        "Response format:\n"
        "1. Quick verdict\n"
        "2. Key technical differences\n"
        "3. Daily usability in Dubai\n"
        "4. Who should buy Vehicle A\n"
        "5. Who should buy Vehicle B\n"
        "6. Final recommendation\n"
        "If important specs are missing, explicitly say that."
    )

    def build_messages(self, car1_specs: dict, car2_specs: dict) -> list[dict]:
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": self.user_template.format(
                    car1=format_car_specs(car1_specs),
                    car2=format_car_specs(car2_specs),
                ),
            },
        ]


def groq_is_ready():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL).strip()
    return bool(
        api_key
        and model
        and "your_" not in api_key.lower()
        and "your-" not in model.lower()
    )


def format_car_specs(car):
    identity = f"{car.get('year', 'Unknown')} {car.get('make', '')} {car.get('variant', car.get('model', 'Vehicle'))}".strip()
    lines = [
        f"Name: {identity}",
        f"Base model: {car.get('model', 'Unknown')}",
        f"Detailed specs available: {'Yes' if car.get('has_detailed_specs') else 'No'}",
        f"Source: {car.get('source', 'Unknown')}",
    ]

    display_specs = car.get("display_specs") or []
    if display_specs:
        lines.append("Technical specs:")
        for item in display_specs:
            lines.append(f"- {item.get('label', item.get('key', 'Spec'))}: {item.get('value', 'N/A')}")

    raw_specs = car.get("raw_specs") or {}
    extra_fields = []
    for key, value in raw_specs.items():
        if key in {"Model", "Make", "Year", "BaseModel"}:
            continue
        if any(item.get("key") == key for item in display_specs):
            continue
        extra_fields.append(f"- {key}: {value}")

    if extra_fields:
        lines.append("Additional fields:")
        lines.extend(extra_fields[:8])

    return "\n".join(lines)


def _numeric_value(car, key):
    raw_value = (car.get("raw_specs") or {}).get(key)
    if raw_value is None:
        return None
    cleaned = str(raw_value).split("/")[0].strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _body_style_hint(car):
    variant = (car.get("variant") or "").upper()
    for body_style in ("SUV", "SEDAN", "COUPE", "HATCHBACK", "WAGON", "CONVERTIBLE", "CABRIOLET"):
        if body_style in variant:
            return body_style.title()
    return "Vehicle"


def build_local_preview(car1_specs, car2_specs):
    name1 = f"{car1_specs.get('year', '')} {car1_specs.get('make', '')} {car1_specs.get('variant', car1_specs.get('model', 'Vehicle A'))}".strip()
    name2 = f"{car2_specs.get('year', '')} {car2_specs.get('make', '')} {car2_specs.get('variant', car2_specs.get('model', 'Vehicle B'))}".strip()

    insights = [
        "Groq is not configured yet, so this is a local preview based on the retrieved specs.",
        "",
        f"Quick verdict: {name1} and {name2} serve different priorities unless their dimensions are nearly identical.",
    ]

    length1 = _numeric_value(car1_specs, "OL")
    length2 = _numeric_value(car2_specs, "OL")
    weight1 = _numeric_value(car1_specs, "CW")
    weight2 = _numeric_value(car2_specs, "CW")
    wheelbase1 = _numeric_value(car1_specs, "WB")
    wheelbase2 = _numeric_value(car2_specs, "WB")

    if length1 and length2:
        longer = name1 if length1 > length2 else name2
        insights.append(f"Size: {longer} is longer, which usually helps cabin presence but can make tight parking less convenient.")

    if wheelbase1 and wheelbase2:
        more_stable = name1 if wheelbase1 > wheelbase2 else name2
        insights.append(f"Ride character: {more_stable} has the longer wheelbase, which often supports better highway composure.")

    if weight1 and weight2:
        lighter = name1 if weight1 < weight2 else name2
        insights.append(f"Agility vs heft: {lighter} is lighter on paper, which can help responsiveness and ease around the city.")

    body1 = _body_style_hint(car1_specs)
    body2 = _body_style_hint(car2_specs)
    insights.append(
        f"Dubai lens: a {body1.lower()} can feel more compact and easier for urban driving, while a {body2.lower()} may suit family space or long highway runs depending on the exact trim."
    )
    insights.append(
        "Recommendation: once you add a valid GROQ_API_KEY, the app will generate a more nuanced Dubai-specific recommendation using the same spec context."
    )

    return "\n\n".join(insights)


class GroqCarComparisonEngine:
    def __init__(self):
        self.prompt = ReusablePrompt()
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL).strip() or GROQ_DEFAULT_MODEL
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "900"))

    @property
    def is_ready(self):
        return groq_is_ready()

    def get_car_comparison_analysis(self, car1_specs, car2_specs):
        if not self.is_ready:
            return {
                "analysis": build_local_preview(car1_specs, car2_specs),
                "model": self.model,
                "groq_configured": False,
                "mode": "local-preview",
            }

        if Groq is None:
            raise RuntimeError(
                "The groq package is not installed. Run pip install -r requirements.txt."
            )

        client = Groq(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=self.prompt.build_messages(car1_specs, car2_specs),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        analysis = response.choices[0].message.content.strip()
        return {
            "analysis": analysis,
            "model": self.model,
            "groq_configured": True,
            "mode": "groq",
        }


def get_car_comparison_analysis(car1_specs, car2_specs, logger=None):
    engine = GroqCarComparisonEngine()
    result = engine.get_car_comparison_analysis(car1_specs, car2_specs)
    if logger:
        logger.info(
            "Completed comparison in %s mode using model %s",
            result["mode"],
            result["model"],
        )
    return result
