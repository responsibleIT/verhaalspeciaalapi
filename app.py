from flask import Flask, jsonify, request
import os
from dataclasses import dataclass
from typing import List
import os
import openai

app = Flask(__name__)

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/generateAct', methods=['POST'])
def generateAct():
    """
    Expects JSON with:
      - characters: array of objects (Character[]) 
          Each character might have: { "name": str, "attributes": [str], "readingLevel": str }
      - location: string
      - theme: string
      - previousAct: string
      - actNumber: number (1..3)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400
    
    # Extract the fields
    characters = data.get('characters', [])
    group = data.get('group', 1) 
    location = data.get('location', '')
    theme = data.get('theme', '')
    previous_act = data.get('previousAct', '')
    act_number = data.get('actNumber', 1)

    #Reading levels
    level_one = 'Leesniveau 1: Tekst bestaat uit korte woorden die je precies zo schrijft zoals je ze uitspreekt. Voorbeelden hiervan zijn maan, bos, man, roos. Er mogen dus geen woorden voorkomen met bijvoorbeeld sch- en -ng en -nk, -b, -d(t), -ch(t), -ooi, -aai, -oei, -eeuw, -ieuw, -uw. De zinnen zijn zo kort mogelijk. Elke zin begint op een nieuwe regel. Er komen geen in hoofdletters voor, dus alle woorden worden met kleine letters geschreven.'

    level_two = 'Leesniveau 2: Tekst bestaat uit één- en tweelettergrepige woorden. Woorden met -sch en -ng mogen voorkomen.  Woorden mogen voorkomen eindigend op -nk, -b, -d(t), -ch(t), -ooi, -aai, -oei, -eeuw, -ieuw, -uw. Een-. Ook mogen tweelettergrepige woorden met twee of drie medeklinkers na elkaar zoals staart, botst, sprong, bankje, knappe, winkel  Er mogen ook enkele makkelijke drielettergrepige woorden voorkomen, zoals sinterklaas. De zinnen zijn meestal kort. Soms mogen samengestelde zinnen voorkomen. Hoofdletters worden gebruikt.'

    level_three = 'Leesniveau 3: Er mogen woorden gebruikt worden met 3 of meer lettergrepen. De zinnen mogen langer zijn. De zinnen kunnen bestaan uit een hoofdzin met een bijzin. Gebruik van leenwoorden, zoals bureau, horloge, chauffeur is beperkt toegestaan. Ook eenvoudige leesmoeilijkheden van leenwoorden komen voor: i en y uitgesproken als ie; c uitgesproken als k of als s. Zinnen mogen beginnen op dezelfde regel. Samengestelde zinnen mogen voorkomen. Hoofdletters worden gebruikt.'

    level_four = 'Leesniveau 4: Er zijn geen beperkingen in woorden en zinslengte. Lastig te lezen leenwoorden (gamen), onbekende woorden (ov-pas, ornament) en leestekens (ideeën, ruïne) komen meer voor. Woorden eindigend op -ele, -eaal, -ueel, -iaal of -ieel komen voor. Ook woorden met een trema komen voor. Ook woorden beginnend met /ch/ uitgesproken als /sj/, eindigend op –ge, uitgesproken als /zje/, eindigend op –isch, woorden met klinkerreeks, leenwoorden met eau, é of è. Hoofdletters worden gebruikt.'
    
    #These are the variables from the front end about the story . 
    child = Character(characters[0]['id'], characters[0]['name'], characters[0]['attributes'], characters[0]['readingLevel']) #Child
    parent = Character(characters[1]['id'], characters[1]['name'], characters[1]['attributes'], characters[1]['readingLevel']) #Parent
    plot = theme
    setting = location

    # These are the input variables from the front end for the reading level
    parent.readingLevel = level_four # 1 2 3 4 based on reading level settings 

    if group < 4:
        child.readingLevel = level_one
        print(child.readingLevel)
    elif group == 4:
        child.readingLevel = level_two
        print(child.readingLevel)
    elif group <= 6:
        child.readingLevel = level_three
        print(child.readingLevel)
    elif group <= 8:
        child.readingLevel = level_four
        print(child.readingLevel)

    #update reading levels
    basic_prompt_v3 =f'''Je bent een kinderboekenschrijver. 
    Je schrijft een verhaal het Nederlands waarbij je de drie-hoofdstukken-structuur van een toneelstuk volgt.
    Dit is een scriptdialoog tussen twee personages en er is een Verteller die de scène schetst. 

    Het leesniveau van de verteller is {parent.readingLevel}.

    Er zijn twee karakers die ieder een eigen leesniveau hebben. Hierna volgen de regels per niveau. Daarna wordt aangegeven welk niveau ieder personage heeft. 
    Dit is een beschrijving van personage {child.name}.
    Het leesniveau van personage {child.name} is niveau {child.readingLevel}, dus houd het taalgebruik op dat niveau voor dit personage. Gebruik hiervoor de omschrijving van de hiervoor genoemde niveuas
    Dit is een beschrijving van personage {parent}.
    Het leesniveau van personage {parent} is niveau {parent.readingLevel}, dus houd het taalgebruik op dat niveau voor dit personage. Gebruik hiervoor de omschrijving van de hiervoor genoemde niveaus houdt het hoofdstuk bij twee zinnen per karakter.

    De algemene verhaallijn is: {plot}.
    De setting van het verhaal is: {setting}.

    Gebruik de volgende regels om te output te structureren:
    Iedere zin of paragraaf van het verhaal moet bij de Verteller, {child.name} of {parent.name} horen. 
    De verteller wordt altijd aangeduid als Verteller. Gebruik het format 0 | Verteller | tekst

    Voeg voor personage {child.name} het volgende format toe: 1 | {child.name} | tekst
    Voeg voor personage {parent.name} het volgende format toe: 2 | {parent.name} | tekst
    Aan het einde van het hoofdstuk moet de verteller een vraag stellen aan een van de personages over de voorgaande dialoog.
    Begin het hoofdstuk duidelijk met het nummer van het hoofdstuk. Bijvoorbeeld: 'Hoofdstuk 1'.
    Zorg ervoor dat de personages hetzelfde blijven in de verschillende hoofdstukken en dat ze weten wat er gezegd is.
    Voeg geen uitleg toe, alleen de dialoog.
    Voeg geen nieuwe personages of settings toe aan de dialoog.
    De allereerste regel van de tekst moet een gegenereerde titel zijn. Gebruik alleen letters en spaties, in de titel staat niet het woord 'titel'.
    Gebruik geen speciale tekens in de tekst, alleen letters, spaties en nieuwe regels.
    Voeg na het verhaal eerst een vraag toe die de verteller stelt aan een van de personages over de voorgaande dialoog.
    Doe dit in de vorm van: 0 | Verteller | Vraag: (de verzonnen vraag over de act).
    Voeg na de vraag het juiste antwoord toe op de vraag van de verteller.
    Doe dit in de vorm van: 0 | Verteller | Antwoord: (het verzonnen antwoord op de vraag van de verteller).
    Geef als allerlaatst na het antwoord een prompt mee die gebruikt kan worden voor het genereren van een afbeelding over de dialoog.
    Doe dit in de vorm van een string: 0 | Verteller | Prompt: (de verzonnen prompt voor de afbeelding).
    '''

    #Chapter prompts
    act_1 = f'''Dit is het eerste hoofdstuk van drie, zorg dus dat het verhaal verder kan gaan.'''
    act_2 = f'''Dit is het tweede hoofdstuk van drie. Ga door op het eerste hoofdstuk wat je uit deze tekst haalt: {previous_act}. Zorg dat het verhaal verder kan gaan in hoofdstuk 3.'''
    act_3 = f'''Dit is het laatste hoofdstuk dus zorg voor een goed en happy einde. Ga door met het verhaal gebaseerd op hoofdstuk 1 en 2 wat je uit de deze tekst haalt: {previous_act}'''

    #Function to call the OpenAI API
    def create_chat_completion(prompt, model="gpt-4"):
        # Create the chat completion
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
                ],
            model=model,

        )
        # Return the generated response
        chapter = chat_completion.choices[0].message.content
        return chapter
        
    #Function to parse chapter into lines object, return lines object
    def parse_chapter(act):
        lines = act.split('\n')
        lines = [line.split('|') for line in lines]
        lines = [Line(int(line[0].strip()), line[2].strip()) for line in lines if len(line) == 3]
        return lines
    
    #Function for parsing the title of the act
    def parse_title(act):
        title = act.split('\n')[0]
        return title
    
    #Function for parsing the image prompt of the act
    def parse_image_prompt(lines):
        image_prompt = lines[-1]
        return image_prompt
    
    #Function for parsing the question of the act
    def parse_question(lines):
        question = lines[-3]
        return question
    
    #Function for parsing the answer of the act
    def parse_answer(lines):
        answer = lines[-2]
        return answer
    
    #Function to generate an act
    def generate_act(act_number):
        if act_number == 1:
            prompt = basic_prompt_v3 + act_1
        elif act_number == 2:
            prompt = basic_prompt_v3 + act_2
        elif act_number == 3:
            prompt = basic_prompt_v3 + act_3

        chapter = create_chat_completion(prompt)
        print(chapter)
        lines = parse_chapter(chapter)
        title = parse_title(chapter)
        image_prompt = parse_image_prompt(lines)
        question = parse_question(lines)
        answer = parse_answer(lines)
        act = Act(act_number, title, lines[:-3], image_prompt, question, answer)
        return act
    
    #Generate the act
    act = generate_act(act_number)
    return jsonify(act), 200


@app.route('/calculateReadingLevel', methods=['POST'])
def calculateReadingLevel():
    """
    Expects JSON with:
      - originalText: string
      - spokenText: string
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    # Extract the fields
    original_text = data.get('originalText', '')
    spoken_text = data.get('spokenText', '')

    #Prompt for OpenAI API
    system_prompt = '''Je bent een expert in het beoordelen van teksten voor kinderboeken. Je gaat een tekst beoordelen of deze aan een bepaald niveau voldoet.'''
    
    #Reading levels
    level_one = 'Leesniveau 1: Tekst bestaat uit korte woorden die je precies zo schrijft zoals je ze uitspreekt. Voorbeelden hiervan zijn maan, bos, man, roos. Er mogen dus geen woorden voorkomen met bijvoorbeeld sch- en -ng en -nk, -b, -d(t), -ch(t), -ooi, -aai, -oei, -eeuw, -ieuw, -uw. De zinnen zijn zo kort mogelijk. Elke zin begint op een nieuwe regel. Er komen geen in hoofdletters voor, dus alle woorden worden met kleine letters geschreven.'
    level_two = 'Leesniveau 2: Tekst bestaat uit één- en tweelettergrepige woorden. Woorden met -sch en -ng mogen voorkomen.  Woorden mogen voorkomen eindigend op -nk, -b, -d(t), -ch(t), -ooi, -aai, -oei, -eeuw, -ieuw, -uw. Een-. Ook mogen tweelettergrepige woorden met twee of drie medeklinkers na elkaar zoals staart, botst, sprong, bankje, knappe, winkel  Er mogen ook enkele makkelijke drielettergrepige woorden voorkomen, zoals sinterklaas. De zinnen zijn meestal kort. Soms mogen samengestelde zinnen voorkomen. Hoofdletters worden gebruikt.'
    level_three = 'Leesniveau 3: Er mogen woorden gebruikt worden met 3 of meer lettergrepen. De zinnen mogen langer zijn. De zinnen kunnen bestaan uit een hoofdzin met een bijzin. Gebruik van leenwoorden, zoals bureau, horloge, chauffeur is beperkt toegestaan. Ook eenvoudige leesmoeilijkheden van leenwoorden komen voor: i en y uitgesproken als ie; c uitgesproken als k of als s. Zinnen mogen beginnen op dezelfde regel. Samengestelde zinnen mogen voorkomen. Hoofdletters worden gebruikt.'
    level_four = 'Leesniveau 4: Er zijn geen beperkingen in woorden en zinslengte. Lastig te lezen leenwoorden (gamen), onbekende woorden (ov-pas, ornament) en leestekens (ideeën, ruïne) komen meer voor. Woorden eindigend op -ele, -eaal, -ueel, -iaal of -ieel komen voor. Ook woorden met een trema komen voor. Ook woorden beginnend met /ch/ uitgesproken als /sj/, eindigend op –ge, uitgesproken als /zje/, eindigend op –isch, woorden met klinkerreeks, leenwoorden met eau, é of è. Hoofdletters worden gebruikt.'
    
    leesniveaus = level_one + level_two + level_three + level_four

    #Prompt for OpenAI API
    prompt = system_prompt + leesniveaus + "Analyseer op welk leeniveau. Antwoord als eerste het leesniveua en beschrijf daarna je redenering. De woorden: Verteller, ENDOFACT, char1, char2, Hoofdstuk neem je NIET mee in je beoordeling."  + generated_text

    #Function to call the OpenAI API
    def create_chat_completion(prompt, model="gpt-4o"):
        # Create the chat completion
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
                ],
            model=model,

        )
        # Return the generated response
        chapter = chat_completion.choices[0].message.content
        return chapter

    return jsonify({}), 200

@dataclass
class Character:
    """
    Represents a character in the story.
    id: 0 = Narrator, 1 = User 1, 2 = User 2
    """
    id: int
    name: str
    attributes: List[str]
    readingLevel: str


@dataclass
class Line:
    """
    Represents a single line of dialogue or text.
    """
    characterId: int
    line: str


@dataclass
class Act:
    """
    Represents an act or scene, containing multiple lines.
    """
    act: int
    title: str
    lines: List[Line]
    imagePrompt: str
    question: str
    answer: str

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if not set
    app.run(host="0.0.0.0", port=port)
