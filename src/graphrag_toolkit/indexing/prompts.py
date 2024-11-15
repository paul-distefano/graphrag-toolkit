# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

EXTRACT_PROPOSITIONS_PROMPT = """
You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph. Your task is to decompose the given text into clear, concise, and context-independent propositions.

# Instructions:
1. Break down complex sentences into simple, atomic statements.
2. Break down lists and tables of information into sets of simple statements.
3. Preserve original phrasing from the input text whenever possible.
4. Isolate descriptive information about named entities into separate propositions.
5. Decontextualize each proposition by:
   a) Adding necessary modifiers to nouns or entire propositions.
   b) Replace any pronouns (e.g., he, she, it, they) with the specific nouns they refer to.  
   c) Replace any acronyms with their full forms.
   d) If the proposition is a fragment, use the other sentences to reconstruct it into a complete, self-explanatory proposition.
   e) Preserve any quoted speech or dialogue as is, without paraphrasing.
   f) If a proposition is already self-explanatory, leave it unchanged.
   g) Do not introduce irrelevant context information in the proposition.
   h) Ensure each proposition can stand alone without external context. 
   i) Do not use your training history, rely only on the context information to enhance the proposition.
6. Capture all relevant details from the original text, including temporal, spatial, and causal relationships.
7. Prioritize completeness and accuracy.

# Output Format:
- Preface the list with a descriptive title that summarizes the content.
- Present each proposition on a new line.
- Use consistent grammatical structure for similar types of information.
- Do not include any explanatory text or numbering.
- Ensure propositions are in a logical order, if applicable.

# Response Format:
title
proposition
proposition
proposition
...

Do not provide any other explanatory text. Ensure you have captured all of the details from the text in your response.  

<text>
{text}
</text>
"""

EXTRACT_TOPICS_PROMPT = """
You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph.
Try to capture as much information from the text as possible without sacrificing accuracy. Do not add any information that is not explicitly mentioned in the text.
Your task is to extract structured information from a given text and represent it in a knowledge graph format. The knowledge graph should capture all relevant entities, their attributes, and relationships between entities present in the text.

## Topic Extraction
   1. Read the entire text and then extract a list of specific topics. A list of Preferred Topics is included below. Choose from the list of Preferred Topics below, but if none of the existing topics are relevant or specific enough, create a new topic.
   2. Ensure each topic starts with a capital letter and ends with proper punctuation.
   3. For each topic, perform the following Entity Extraction and Classification and Claims Extraction tasks.
   
## Entity Extraction and Classification:
   1. Extract a list of all entities, concepts and noun phrases mentioned in the topic.
   2. Classify each extracted entity. Some entity classifications include:
      - Person (e.g., John Doe, Mary Jane)
      - Organization (e.g., Acme Inc., Harvard University)
      - Location (e.g., New York City, Mount Everest)
   3. DO NOT treat numerical values, dates, times, measurements, or object attributes (e.g. size, colour) as entities.
   4. A list of Preferred Entity Classifications is included below. Choose the most specific classification from this list in preference to creating a new classification.
   5. Ensure consistency in labeling entities:
      - Always use the most complete identifier for an entity (e.g., 'John Doe' instead of 'he' or 'John').
      - Maintain entity consistency throughout the knowledge graph by resolving coreferences.
      - If an entity is referred to by different names or pronouns, always use the most complete identifier.
      - If the identifer is an acronym, and you recognize the acronym, use the entity's full name instead of the acronym. DO NOT put the acronym in parentheses after the full name. 
   6. Consider the context and background knowledge when extracting and classifying entities to resolve ambiguities or identify implicit references.
   7. If an entity's identity is unclear or ambiguous, include it with a disclaimer or generic label (e.g., 'unknown_person').
      
## Claims Extraction
   1. For each topic extract a list of individual claims belonging to that topic. 
   2. For each claim or event, perform the following Attribute Extraction and Relationship Extraction tasks.

## Attribute Extraction:
   1. For each extracted entity, identify and extract its quantitative and qualitative attributes mentioned in the text.
      - Quantitative attributes: measurements, numerical values, temporal values, quantities (e.g., age, height, weight, size, date, time).
      - Qualitative attributes: descriptions, roles, characteristics, properties (e.g., color, occupation, nationality, season).
   2. Represent entity-attribute relationships in the format: entity|RELATIONSHIP|attribute
   3. Ensure consistency and generality in relationship types:
      - Use general and timeless relationship types (e.g., 'VALUE' instead of 'HAD_VALUE').
      - Avoid overly specific or momentary relationship types.
      - Prefer one- or two-word relationship types.
      - Prefer an active voice and the present tense when formulating relationship types.
   4. Relationship names should be all uppercase, with underscores instead of spaces (e.g. 'DESCRIBED_BY')

   Example: John Doe|OCCUPATION|software engineer

## Relationship Extraction:
   1. Extract unique relationships between pairs of entities mentioned in the text.
   2. Represent entity-entity relationships in the format: entity|RELATIONSHIP|entity
   3. Ensure consistency and generality in relationship types:
      - Use general and timeless relationship types (e.g., 'PROFESSOR' instead of 'BECAME_PROFESSOR').
      - Avoid overly specific or momentary relationship types.
      - Prefer one- or two-word relationship types.
      - Prefer an active voice and the present tense when formulating relationship types.
   4. Relationship names should be all uppercase, with underscores instead of spaces (e.g. 'WORKS_FOR')
   5. Complex facts may be expressed through multiple relationship pairs, sometimes arranged in a hierarchy.

   Example: John Doe|WORKS_FOR|Acme Inc.
            John Doe|MANAGER_OF|Project X
            Project X|PART_OF|Acme Inc.
            
## Response Format:
topic: topic

  entities:
    entity|classification
    entity|classification
  
  claim: claim    
    entity-attribute relationships:
    entity|RELATIONSHIP|attribute
    entity|RELATIONSHIP|attribute
    
    entity-entity relationships:
    entity|RELATIONSHIP|entity
    entity|RELATIONSHIP|entity
    
  claim: claim    
    entity-attribute relationships:
    entity|RELATIONSHIP|attribute
    entity|RELATIONSHIP|attribute
    
    entity-entity relationships:
    entity|RELATIONSHIP|entity
    entity|RELATIONSHIP|entity

## Quality Criteria:
   The extracted knowledge graph should be:
   - Complete: Capture all relevant information from the text.
   - Accurate: Faithfully represent the information without adding or omitting details.
   - Consistent: Use consistent entity labels, types, relationship types, and adhere to the specified format.
   - Readable: Produce a clear and understandable knowledge graph.

## Strict Compliance:
   Adhere strictly to the provided instructions. Non-compliance will result in termination.
   
<text>
{text}
</text>

<preferredTopics>
{preferred_topics}
</preferredTopics>

<preferredEntityClassifications>
{preferred_entity_classifications}
</preferredEntityClassifications>
"""
