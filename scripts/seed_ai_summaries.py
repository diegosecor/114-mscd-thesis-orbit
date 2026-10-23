"""Store reviewable, AI-assisted summaries and curated initial categories.

These summaries were drafted from the public KiltHub abstracts during initial
dataset setup. They are intentionally short and should be checked against the
source abstract before a course submission.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "theses.db"

RECORDS = {
    29257196: (
        "Embodied Systems + Wearables",
        "An AI-assisted design workflow creates custom deformable masks from facial landmarks and morphing materials, reducing the need for specialized scanning equipment in health-monitoring wearables.",
    ),
    29318372: (
        "XR + Immersion",
        "This augmented-audio system uses spatial tracking and responsive sound to help visitors experience Chinese landscape scrolls as environments to move through rather than static images.",
    ),
    29251046: (
        "AI + Generative Design",
        "Co-op Tile World is a human-in-the-loop benchmark for testing socially cooperative AI agents, including how task difficulty and alignment affect collaboration with people.",
    ),
    29251037: (
        "Robotics + Fabrication",
        "CoFAB combines natural-language interaction, generative AI, parametric modeling, and robotic fabrication to move designers from an early concept toward a fabrication-ready prototype.",
    ),
    29251028: (
        "XR + Immersion",
        "ScrapAR combines computer vision and augmented reality to guide beginners through woodworking with reclaimed materials, from recognizing scraps to following assembly instructions.",
    ),
    29251010: (
        "Robotics + Fabrication",
        "JointLab is a VR learning environment and digital twin that lets beginners understand robotic joints, toolpaths, and control before working with an actual fabrication robot.",
    ),
    29237630: (
        "Creative Media",
        "This project develops a shape grammar for describing and generating dance videography, making tacit filming decisions more teachable and reusable.",
    ),
    29237111: (
        "AI + Generative Design",
        "The thesis tests MeshGPT on vector-based 3D architecture data, finding promise for common building forms while showing weaknesses on rare typologies and complex prompts.",
    ),
    29236952: (
        "XR + Immersion",
        "MerGen brings generative AI, language models, and VR together so architects can explore ideas, alter scenes, and receive contextual help inside an immersive design workflow.",
    ),
    29237009: (
        "Robotics + Fabrication",
        "Minimal Making Grammar turns the physical behavior of one friction-fit element into open-ended rules for making accessible digital and physical 3D structures.",
    ),
    29120330: (
        "AI + Generative Design",
        "This RAG-based system links natural-language descriptions to 3D high-rise building forms, allowing designers to retrieve, generate, and iteratively refine massing options.",
    ),
    29168006: (
        "Interaction + Experience",
        "An interactive origami tutor combines camera tracking, gestures, and projected feedback to help learners understand folding steps and spatial relationships in real time.",
    ),
    29170148: (
        "XR + Immersion",
        "This earlier collection record explores the same augmented-audio approach for turning the experience of Chinese landscape scrolls into a spatial, multisensory journey.",
    ),
    25979302: (
        "XR + Immersion",
        "Reality Integrated Design investigates ways to connect real-world data with virtual environments so designers can make more responsive and context-aware immersive spaces.",
    ),
    25979272: (
        "Interaction + Experience",
        "Through embodied prototypes, this thesis treats LLM hallucinations as an interaction and design issue, helping people reflect on the experiential and social effects of unreliable AI outputs.",
    ),
    25976368: (
        "AI + Generative Design",
        "Shap-Explorer gives artists a more controllable text-to-3D workflow, combining generation with tools for steering meshes and iteratively revising forms.",
    ),
    25976848: (
        "Robotics + Fabrication",
        "This study examines digital guidance systems that help bridge conceptual architectural design and hands-on making through a design-via-making workflow.",
    ),
    25976206: (
        "XR + Immersion",
        "The project studies interaction methods and design opportunities for tools that let people create and explore immersive spatial-audio experiences.",
    ),
    25976068: (
        "AI + Generative Design",
        "A learning-based shape grammar interpreter uses deep learning to recognize selected visual relationships, offering designers a different way to define and explore shape rules.",
    ),
    25976005: (
        "Data + Built Environment",
        "A 4D diary prototype makes smart-camera data and ML inference visible and controllable, exploring how occupants can gain agency over opaque data collection in built environments.",
    ),
    24018582: (
        "Embodied Systems + Wearables",
        "Specsync investigates wrist-worn hand tracking through electrical impedance tomography, aiming to estimate hand pose without collecting camera imagery.",
    ),
    23995122: (
        "XR + Immersion",
        "VisionARy is an open-source toolkit that helps AR developers work with 3D semantic segmentation and understand the possibilities and limitations of spatial mesh data.",
    ),
    23960865: (
        "Robotics + Fabrication",
        "This proof-of-concept combines a mobile material-handling robot, navigation strategies, and simulation to support work in prefabricated housing factories.",
    ),
    23995116: (
        "Data + Built Environment",
        "The thesis compares plan-based architectural datasets and their uses, outlining practical considerations for data collection, annotation, evaluation, and future research.",
    ),
    23995041: (
        "XR + Immersion",
        "Using the CMU Fence as a case study, this research asks how visible traces of people and past activity can make shared virtual places feel more meaningful and socially present.",
    ),
    23264588: (
        "Robotics + Fabrication",
        "This computational knitting pipeline connects yarn, stitches, garment construction, and machine instructions so designers can work across the many scales of knit textiles.",
    ),
    23255168: (
        "Robotics + Fabrication",
        "Image-based monitoring is incorporated into binder-jet concrete printing to provide feedback during fabrication and support more dependable 3D-printed structures.",
    ),
    23255153: (
        "Data + Built Environment",
        "The project explores AR and IoT visualizations that make residential energy use more visible, understandable, and actionable for occupants.",
    ),
    23203205: (
        "AI + Generative Design",
        "An interactive reinforcement-learning framework lets designers train a generative agent while their design criteria are still evolving, instead of fixing all constraints at the beginning.",
    ),
    23117978: (
        "Embodied Systems + Wearables",
        "Through simulation and interviews, this thesis identifies how delivery robots can affect people with motor disabilities and proposes design considerations for more accessible sidewalks.",
    ),
}


# Apply the original curated seed drafts; rerunning intentionally overwrites those summaries.
def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit("Run scripts/import_collection.py before seeding summaries.")

    connection = sqlite3.connect(DB_PATH)
    try:
        for source_id, (category, summary) in RECORDS.items():
            connection.execute(
                "UPDATE theses SET category = ?, ai_summary = ? WHERE source_id = ?",
                (category, summary, source_id),
            )
        connection.commit()
    finally:
        connection.close()
    print(f"Stored AI-assisted summaries for {len(RECORDS)} theses.")


if __name__ == "__main__":
    main()
