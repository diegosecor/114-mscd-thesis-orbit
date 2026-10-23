"""Seed reviewed AI-assisted descriptions for the additional public archive records.

Each description was drafted from that record's KiltHub source_abstract.
Only empty summaries are populated, so rerunning preserves later user edits.
The original 30 records are maintained separately in seed_ai_summaries.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "theses.db"

RECORDS = {
    23113175: (
        "XR + Immersion",
        "Using a VR escape room, this study compares environments that imitate reality with ones that depart from it. Experiments investigate how these different design approaches affect the immersive game experience.",
    ),
    23103263: (
        "Interaction + Experience",
        "This thesis proposes two-way interactions between physical and digital environments. An interactive system and a device demonstrate how the sensory and structural affordances of physical objects can connect with digital information and capabilities.",
    ),
    23100506: (
        "Robotics + Fabrication",
        "A responsive robotic assembly framework combines material analysis, parametric design, and adaptive path planning to work with irregular raw branches. Prototypes investigate how feedback can coordinate design choices and robotic pick-and-place operations.",
    ),
    23099876: (
        "Data + Built Environment",
        "This project generates synthetic construction-site images in Unity for detecting recyclable bricks. Experiments compare real and synthetic training data, finding benefits from combining them while identifying limitations of replacing real data entirely.",
    ),
    23065484: (
        "Data + Built Environment",
        "The thesis investigates how building information models can incorporate live sensor data as digital twins. A LiDAR-to-BIM service motivates a distributed microservices architecture designed to improve dependency management, flexibility, and scalability.",
    ),
    23064968: (
        "AI + Generative Design",
        "Two studies examine generative image AI in sketch-based design and designer-client communication. They explore its role in early inspiration, the difficulties designers encounter, and opportunities to improve AI tools for collaborative design.",
    ),
    23019806: (
        "Interaction + Experience",
        "Co-creative workshops explore how Pittsburgh community members understand public algorithms used in consequential services. The project introduces a Tangible Poster as a possible way to gather community opinions and support discussion.",
    ),
    23016341: (
        "AI + Generative Design",
        "This thesis explores human-agent co-creation in virtual reality through reinforcement learning. A design framework uses human demonstrations to shape agent behavior and investigates how such agents might participate in open-ended creative tasks.",
    ),
    23015195: (
        "AI + Generative Design",
        "Three design experiments investigate machine-learning latent spaces as environments for exploring volumetric forms. The work compares design representations, fabricates a generated chair, and experiments with ways to visualize and interact with generative systems.",
    ),
    22825592: (
        "Computational Design",
        "An autobiographical account follows the development of an interactive inflatable structure. Through artifacts, reflections, and conversations, the thesis examines how nonlinear changes in direction shape design research and how those changes can be documented.",
    ),
    22825328: (
        "Creative Media",
        "The project combines Neural Radiance Fields with image style-transfer methods to transform reconstructed 3D scenes. It compares technical and aesthetic results and explores applications in architectural visualization and art creation.",
    ),
    21938423: (
        "Data + Built Environment",
        "This research develops a point-cloud processing and visualization pipeline centered on human recognition. It compares learning-based methods and tests visualization alternatives through questions about objects, meaning, and spatial understanding.",
    ),
    21928485: (
        "XR + Immersion",
        "A location-based augmented reality application overlays cultural and historical information around Pittsburgh's Freedom Corner. The project explores how digital experiences can make intangible community heritage visible within the physical landscape.",
    ),
    21331158: (
        "Interaction + Experience",
        "This thesis explores multisensory digital experiences as invitations to social interaction in public space. Prototypes include artificial grass used as a sound interface and a computer-vision-enabled sand table for composing sound.",
    ),
    21342642: (
        "Interaction + Experience",
        "Three everyday interactions explore more attentive relationships with time, place, and other people: an unraveling textile calendar, an orientation-based radio, and a sky-photograph clock. The thesis reflects on the value of deliberate effort in interaction.",
    ),
    21391395: (
        "Data + Built Environment",
        "The thesis critically examines graph representations and floor-plan datasets used in architectural machine learning. Literature research, reconstructed software, and computational experiments reveal how representational choices shape the possibilities and limitations of generative and analytical tools.",
    ),
    21375987: (
        "Interaction + Experience",
        "Interactive visualization prototypes support planning, operations, and scientific exploration for the MoonRanger lunar rover mission. The thesis examines how visual tools can help teams make decisions and understand remote planetary environments.",
    ),
    21365778: (
        "Embodied Systems + Wearables",
        "A collaborative design exploration with a female prosthetic user considers expressive and emotional needs alongside physical function. Speculative morphing prosthetics are developed as virtual models and experienced on the body through augmented reality.",
    ),
    21357153: (
        "Creative Media",
        "Video recordings of daily walks through Pittsburgh's Shadyside neighborhood become material for a computational sound composition. The project maps visual features to sonic parameters, exploring subjective cartography and new ways to experience place over time.",
    ),
    21350691: (
        "Interaction + Experience",
        "ShapeHub is a web platform for collaborative architectural design with branching, version history, and communication features. It explores how online tools can support shared iteration and adapt studio collaboration to digital environments.",
    ),
    21321063: (
        "XR + Immersion",
        "An augmented reality walk at Allegheny Commons West Park presents historical scenes as spatial collages. Visitors assemble viewpoints and choose their own paths, exploring an alternative to linear narratives in digital heritage experiences.",
    ),
    21291672: (
        "Data + Built Environment",
        "A dataset of 313 reconstructed wooden churches supports deep-learning analysis of regional architectural form. The project investigates stylistic relationships and hybrid forms while exploring digital documentation of Ukrainian architectural heritage.",
    ),
    21272700: (
        "Interaction + Experience",
        "Three speculative interactive assemblages explore domestic technology through an autobiographical study of the home. Spatial audio and location-aware tracking offer alternatives for distributing information and designing context-sensitive interactions across the surrounding environment.",
    ),
    21272679: (
        "Computational Design",
        "This thesis introduces a free-form modeling workflow that lets designers intervene in physical constraint optimization. Opening up this usually hidden process aims to expand the design possibilities available within computer-aided modeling.",
    ),
    21209093: (
        "Robotics + Fabrication",
        "Reconfigurable lattice structures combine passive cells with pneumatically actuated units to create motion. An inverse-design tool helps users arrange cells for target behaviors, supporting crawling robots, kinetic sculptures, and physical notification interfaces.",
    ),
    21208226: (
        "Interaction + Experience",
        "Speculative experiments treat everyday nonverbal sounds as interaction materials. A TinyML-enabled helper extends Google Home to recognize events such as sneezes, opening doors, and table taps, inviting new responses to familiar surroundings.",
    ),
    14141738: (
        "Embodied Systems + Wearables",
        "An interactive art-making system pairs children with the mobile social robot Kuri on a projected floor. The thesis explores how robot movement, expression, sound, and light might encourage curiosity and experimentation.",
    ),
    14141702: (
        "XR + Immersion",
        "A mixed reality audio walk at Carrie Furnace combines oral histories and environmental sounds into a spatial soundscape. The project explores open-ended wandering as a way to evoke memories of the post-industrial landscape.",
    ),
    14138024: (
        "Robotics + Fabrication",
        "This thesis simulates multi-drone construction using deep reinforcement learning for collision avoidance. A software package connects the approach to Rhinoceros, with bricklaying and facade-coating experiments demonstrating possible applications.",
    ),
    14138012: (
        "Interaction + Experience",
        "Responsive Layer combines projection mapping and computer vision to make everyday objects respond with digital information. Five prototypes explore object interaction, contextual displays, reminders, and movement tracking without embedding sensors in each object.",
    ),
    14137955: (
        "Robotics + Fabrication",
        "Hybrid Embroidery combines handcraft, computer vision, generative stitching, and CNC fabrication. Turn-based interactions between people and algorithms support improvisation, play, and shared textile creation through direct engagement with materials.",
    ),
    14136008: (
        "AI + Generative Design",
        "A four-step development process guides the creation of generative design software for architects. A basement-parking layout tool demonstrates the approach through variational modeling and optimization, addressing usability and architectural design criteria.",
    ),
    14135963: (
        "Data + Built Environment",
        "This thesis combines graph modeling, Object Process Methodology, and Bayesian networks to represent competing goals in street design. The framework explores uncertainty and relationships between stakeholder values to support constructive problem framing.",
    ),
    14135873: (
        "Data + Built Environment",
        "Technical experiments and industry experience examine how real-estate technology connects algorithms, data, and business models. Case studies explore data scarcity, automated valuation, geographic accuracy, and the wider social and economic context of PropTech.",
    ),
    14135807: (
        "Interaction + Experience",
        "A mixed modeling prototype connects tangible cubes with a graphical 3D interface. Physical voxel arrangements and digital mesh editing support concurrent interaction and iterative design, combining embodied manipulation with parametric control.",
    ),
    14135663: (
        "Creative Media",
        "Two experimental tools let artists directly craft convolutional neural-network kernels and weights. The thesis explores these values as a creative material, documenting opportunities for bespoke feature detectors and limits when constructing more complex networks.",
    ),
    13348091: (
        "AI + Generative Design",
        "A machine-learning prototype explores content-aware image relighting. By considering visual properties relevant to illumination, the project investigates a lightweight editing approach that combines aspects of image processing and rendering.",
    ),
    9981947: (
        "Robotics + Fabrication",
        "An interactive fabrication workflow uses computer vision to detect users' physical changes to an artifact. Updated geometry informs subsequent toolpaths, exploring how hands-on making and machine fabrication can jointly support creative design.",
    ),
    9778436: (
        "Robotics + Fabrication",
        "SimuLearn combines numerical methods and machine learning to predict shape changes in 4D-printed materials. A prototype design tool explores faster, physically informed digital iteration that can reduce dependence on repeated physical prototypes.",
    ),
    8234276: (
        "Interaction + Experience",
        "A portable, low-cost texture scanner captures physical surface detail at microscopic scale for use in design. Technical evaluation and expert case studies explore how 3D texture sampling can strengthen material awareness in digital workflows.",
    ),
    8235539: (
        "XR + Immersion",
        "Wake brings a headset participant, live dancer, and facilitator into a shared mixed reality experience. A user study examines embodied interaction, emotion, and trust, informing design considerations for socially and physically mindful XR.",
    ),
    8235659: (
        "Computational Design",
        "This thesis uses topic modeling, bibliometrics, and interactive visualization to examine computational design as a research field. It investigates topics, keywords, geographic distribution, researcher collaboration, and the field's historical development.",
    ),
    7178417: (
        "Data + Built Environment",
        "The thesis explores machine learning for space-syntax analysis, focusing on privacy in house plans. Spatial features, isovists, and graphs inform a proposed framework, with preliminary experiments examining relationships between configuration and intimacy.",
    ),
    7178138: (
        "XR + Immersion",
        "Research in QuiVR and VRChat examines how avatar representation and design decisions relate to harmful social behavior. Subsequent experiments explore abstracted bodies and alternative movement mapping as ways to rethink embodied virtual experiences.",
    ),
    7182206: (
        "Data + Built Environment",
        "A topology-based search engine helps users find architectural plans through spatial relationships. Users draw a building's spatial structure, which is converted into a graph and compared with database examples using belief propagation.",
    ),
    7182263: (
        "AI + Generative Design",
        "An interactive genetic algorithm supports a conversational approach to architectural form generation. A prototype incorporates designers' evaluation and modification into computation, exploring a workflow where human creativity and algorithmic optimization inform one another.",
    ),
    6723359: (
        "Embodied Systems + Wearables",
        "A wearable force-feedback device supports room-scale painting in virtual reality. Developed with an artist, the system explores customized haptic feedback, tool affordances, and real-time 3D strokes to expand expressive painting interactions.",
    ),
    7182911: (
        "Computational Design",
        "The iSimp Maya plugin turns dense 3D scans into simpler, editable models using interactive variational shape approximation. Optimization work and a designer workshop explore how this workflow can support creative modeling from physical objects.",
    ),
    7063361: (
        "Data + Built Environment",
        "Case studies in Madrid and Pittsburgh combine computer vision, statistical analysis, and clustering to examine urban space use. The workflow relates spatial features to activity patterns, aiming to inform architectural and urban design decisions.",
    ),
    7182887: (
        "Data + Built Environment",
        "A web-based visualization prototype enables interactive clustering of geolocated data with multidimensional K-means. Infrastructure development, user evaluation, and an application scenario explore its usefulness for architectural design and urban studies.",
    ),
    7178054: (
        "Computational Design",
        "This research explores voxels and tetrahedral meshes as representations for adaptive architectural geometry. A simulation framework investigates how their geometric affordances can support morphological changes in response to context and design decisions.",
    ),
    6723389: (
        "Computational Design",
        "Interviews, software prototypes, and workshops inform a three-part framework for computational design: generating, simulating, and interrogating. The thesis explores how designers can question their tools and imagine more humane alternatives through reflective practice.",
    ),
    6723233: (
        "Data + Built Environment",
        "This thesis investigates interactive visualization of building energy use. Reviews of existing projects and a new interface prototype explore how unusual visual approaches can encourage insight, questioning, and engagement with energy-related issues.",
    ),
    6722939: (
        "Interaction + Experience",
        "A Kinect-based prototype links physical wooden-block arrangements to a live digital voxel model. It combines tactile design interaction with digital views, parametric editing, saved configurations, and basic analysis in a concurrent modeling environment.",
    ),
}


# Fill only empty archive summaries, preserving later user edits.
def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit("Run scripts/import_collection.py --all first.")
    updated = 0
    connection = sqlite3.connect(DB_PATH, timeout=30)
    try:
        for source_id, (category, summary) in RECORDS.items():
            cursor = connection.execute(
                """UPDATE theses SET category = ?, ai_summary = ?
                   WHERE source_id = ? AND TRIM(COALESCE(ai_summary, '')) = ''""",
                (category, summary, source_id),
            )
            updated += cursor.rowcount
        connection.commit()
        missing = connection.execute(
            "SELECT COUNT(*) FROM theses WHERE TRIM(COALESCE(ai_summary, '')) = ''"
        ).fetchone()[0]
    finally:
        connection.close()
    print(f"Stored {updated} additional AI-assisted summaries; {missing} records still lack a summary.")


if __name__ == "__main__":
    main()
