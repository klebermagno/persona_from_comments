from dataclasses import dataclass, field
from comment import Comment
from db_manager import DBManager
import json

@dataclass
class Persona:
    video_title: str = ''
    video_id: str = ''
    name: str = ''
    gender: str = ''
    issues: list = field(default_factory=list)
    wishes: list = field(default_factory=list)
    pains: list = field(default_factory=list)
    expressions: list = field(default_factory=list)
    

class PersonaBuilder:
    
    def __init__(self) -> None:
        self.db = DBManager()
        self.db.connect()
     
    def _get_most_common_persona_name(self, video_id) -> set:        
        genders_count = {'M':0, 'F':0}        
        unique_fullnames = {'F':[], 'M':[]}
        
        for row in self.db.get_comments(video_id):
            comment = Comment(row)
            if not comment.author_clean_name in unique_fullnames:
                genders_count[comment.author_gender] = 1
            else:
                genders_count[comment.author_gender] += 1
            
            unique_fullnames[comment.author_gender].append(comment.author_clean_name)
                
        key_gender = ('M' if genders_count['M'] > genders_count['F'] else 'F')
        names = {}
        key_name = ('',0)
        for name in unique_fullnames[key_gender]:
            firstname = name.split()[0]
            if firstname in names:
                names[firstname] += 1
            else:
                names[firstname] = 1
            
            if names[firstname] >= key_name[1]:
                key_name = (firstname, names[firstname])          
        return (key_name[0], key_gender)    

    def _get_analysis_data(self, video_id) -> dict:
        """Get analysis data from the database"""
        self.db.cur.execute("SELECT issues, wishes, pains, expressions FROM analysis WHERE video_id = ?", (video_id,))
        row = self.db.cur.fetchone()
        
        if row:
            return {
                'issues': json.loads(row[0]) if row[0] else [],
                'wishes': json.loads(row[1]) if row[1] else [],
                'pains': json.loads(row[2]) if row[2] else [],
                'expressions': json.loads(row[3]) if row[3] else []
            }
        return {'issues': [], 'wishes': [], 'pains': [], 'expressions': []}
    
    def _get_video_title(self, video_id) -> str:
         self.db.cur.execute("SELECT title FROM video WHERE video_id = '{}'".format(video_id))
         row = self.db.cur.fetchone()
         return row[0]
        
    def build(self, video_id) -> Persona:
        persona = Persona()
        name = self._get_most_common_persona_name(video_id)
        persona.name = name[0]
        persona.gender = name[1]
        
        # Get analysis data
        analysis = self._get_analysis_data(video_id)
        persona.issues = analysis['issues']
        persona.wishes = analysis['wishes']
        persona.pains = analysis['pains']
        persona.expressions = analysis['expressions']
        
        persona.video_title = self._get_video_title(video_id)
        persona.video_id = video_id
 
        self.db.close()
        
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
    
    def build(self, persona : Persona) -> None:
        html = self.template.format(
            name=persona.name,
            gender=persona.gender,
            issues=persona.issues,
            wishes=persona.wishes,
            pains=persona.pains,
            expressions=persona.expressions,
            video_title=persona.video_title,
            video_id=persona.video_id          
        )
        
        with open('output/Report-{}.html'.format(persona.video_id), 'w', encoding="utf-8") as f:
            f.write(html)
            
            
class Generating:
    
    def execute(self, video_id) -> None:
        builder = PersonaBuilder()
        persona = builder.build(video_id)
        report = PersonaReport()
        report.build(persona)