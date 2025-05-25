import logging
from dataclasses import dataclass, field

# from comment import Comment # Comment class might not be directly needed if using dicts
from .db_manager import DBManager
import json

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    video_title: str = ""
    video_id: str = ""
    name: str = ""
    gender: str = ""
    issues: list = field(default_factory=list)
    wishes: list = field(default_factory=list)
    pains: list = field(default_factory=list)
    expressions: list = field(default_factory=list)


class PersonaBuilder:

    def __init__(self) -> None:
        self.db = DBManager()
        # self.db.connect() # REMOVED

    def _get_most_common_persona_name(
        self, video_id
    ) -> tuple:  # Return type changed to tuple
        logger.debug(f"Calculating most common persona name for video {video_id}")
        genders_count = {"M": 0, "F": 0}
        # Store full names to count unique authors before counting first names
        author_gender_map = (
            {}
        )  # Maps author_clean_name to gender to avoid double counting if name appears with different genders (unlikely)

        comments_data = self.db.get_comments(video_id)  # Returns list of dicts
        for comment_dict in comments_data:
            author_name = comment_dict.get("author_clean_name")
            author_gender = comment_dict.get("author_gender")

            if (
                author_name and author_gender
            ):  # Process only if name and gender are present
                if author_name not in author_gender_map:
                    author_gender_map[author_name] = author_gender
                    genders_count[author_gender] = (
                        genders_count.get(author_gender, 0) + 1
                    )

        if not genders_count or (genders_count["M"] == 0 and genders_count["F"] == 0):
            logger.warning(
                f"No gender data found to determine dominant gender for video {video_id}"
            )
            return ("Unknown", "N/A")

        dominant_gender = "M" if genders_count["M"] >= genders_count["F"] else "F"

        first_names_count = {}
        for author_name, gender in author_gender_map.items():
            if gender == dominant_gender:
                first_name = author_name.split()[0]
                first_names_count[first_name] = first_names_count.get(first_name, 0) + 1

        if not first_names_count:
            logger.warning(
                f"No names found for dominant gender {dominant_gender} for video {video_id}"
            )
            return ("Unknown", dominant_gender)

        most_common_first_name = max(first_names_count, key=first_names_count.get)
        logger.debug(
            f"Most common persona: {most_common_first_name}, Gender: {dominant_gender}"
        )
        return (most_common_first_name, dominant_gender)

    def _get_analysis_data(self, video_id) -> dict:
        """Get analysis data from the database using DBManager method."""
        logger.debug(f"Fetching LLM analysis data for video {video_id}")
        analysis_data = self.db.get_analysis(
            video_id
        )  # This method already returns a dict or None
        if analysis_data:
            return analysis_data
        logger.warning(
            f"No analysis data found for video {video_id}, returning empty structure."
        )
        return {
            "issues": [],
            "wishes": [],
            "pains": [],
            "expressions": [],
        }  # Default if None

    def _get_video_title(self, video_id) -> str:
        logger.debug(f"Fetching video title for video {video_id}")
        title = self.db.get_video_title(
            video_id
        )  # This method returns title or "Unknown Title"
        return title

    def build(self, video_id) -> Persona:
        logger.info(f"Starting persona generation for video {video_id}")
        persona = Persona()

        # Get video title first as it's independent
        persona.video_title = self._get_video_title(video_id)
        persona.video_id = video_id

        # Get demographic data (name, gender)
        # The method get_user_demographics in db_manager.py is more direct for this.
        # Let's use that instead of reimplementing the logic here.
        # name_tuple = self._get_most_common_persona_name(video_id)
        # persona.name = name_tuple[0]
        # persona.gender = name_tuple[1]

        # Using the existing get_user_demographics from DBManager
        db_name, db_gender = self.db.get_user_demographics(video_id)
        persona.name = db_name if db_name else "Unknown"
        persona.gender = (
            db_gender if db_gender else "N/A"
        )  # Ensure gender is 'M' or 'F' or a default

        # Get analysis data
        analysis = self._get_analysis_data(video_id)
        persona.issues = analysis.get("issues", [])  # Use .get for safety
        persona.wishes = analysis.get("wishes", [])
        persona.pains = analysis.get("pains", [])
        persona.expressions = analysis.get("expressions", [])

        # self.db.close() # REMOVED - Handled by DBManager
        logger.info(
            f"Finished persona generation for video {video_id}: {persona.name}, {persona.gender}"
        )
        return persona


class PersonaReport:

    def __init__(self) -> None:
        self.template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .label {{
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div style="margin: 10%;">
                <h1> Generated Persona </h1>
                <table>
                    <tr>
                        <td class="label">Source Video</td>
                        <td>{video_title}</td>
                    </tr>
                    <tr>
                        <td class="label">Video Id</td>
                        <td>{video_id}</td>
                    </tr>
                    <tr>
                        <td class="label">Name</td>
                        <td>{name}</td>
                    </tr>
                    <tr>
                        <td class="label">Gender</td>
                        <td>{gender}</td>
                    </tr>
                    <tr>
                        <td class="label">Issues</td>
                        <td>{issues}</td>
                    </tr>
                    <tr>
                        <td class="label">Wishes</td>
                        <td>{wishes}</td>
                    </tr>
                    <tr>
                        <td class="label">Pains</td>
                        <td>{pains}</td>
                    </tr>
                    <tr>
                        <td class="label">Common Expressions</td>
                        <td>{expressions}</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """

    def build(self, persona: Persona) -> None:
        html = self.template.format(
            name=persona.name,
            gender=persona.gender,
            issues=persona.issues,
            wishes=persona.wishes,
            pains=persona.pains,
            expressions=persona.expressions,
            video_title=persona.video_title,
            video_id=persona.video_id,
        )

        with open(
            "output/Report-{}.html".format(persona.video_id), "w", encoding="utf-8"
        ) as f:
            f.write(html)


class Generating:

    def execute(self, video_id) -> None:
        builder = PersonaBuilder()
        persona = builder.build(video_id)
        report = PersonaReport()
        report.build(persona)
