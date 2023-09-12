from inspect import Attribute
from dataclasses import dataclass
import xmltodict
import json
from PyPDF2 import PdfReader
openedFile = False

def openFile(route, override=False, pdfInfo=""):
  '''
  Abrir el archivo xmi dada la ruta de este 
  '''
  global openedFile
  data = {}
  if openedFile == True and override == False:
      print("Ya hay un archivo abierto, está seguro de que quiere sobrescribir?")
  else:
    with open(route) as xml_file:
        data = xmltodict.parse(xml_file.read())
    xml_file.close()
    json_data = json.dumps(data)
    with open("data.json", "w") as json_file:
            json_file.write(json_data)
    json_file.close()
    print("Archivo cargado exitosamente")
    if pdfInfo != "":
        reader = PdfReader(pdfInfo)
        text = [p.extract_text() for p in reader.pages]
        print("Archivo PDF cargado exitosamente")
        return data, text
    return data

@dataclass
class UMLCLass:
  """Class for UML Class storage"""
  name: str
  xmi_id: str
  attributes : list
  operations : list

@dataclass
class Association:
  """Class for UML Relations storage"""
  name: str
  xmi_id: str
  nl_nexus: list
  id_nexus: list
  directed: bool
  terminals : list

@dataclass
class Terminal:
  """Class for Relations terminals"""
  name: str
  xmi_id: str
  o_type: str
  aggregation: str
  range: list
@dataclass
class Operation:
  """Class for operations"""
  name: str
  visibility: str
  xmi_id: str
  parameters: list

@dataclass
class Parameter:
  """Class for parameters"""
  name: str
  xmi_id: str
  is_unique: bool
  direction: str
  o_type: str

@dataclass
class Attribute:
  """Class for attributes"""
  name: str
  xmi_id: str
  visibility: str
  o_type: str


def filter(data):
  classes = []
  relations = []
  id_lookup = []
  da = data["xmi:XMI"]["uml:Model"]
  projectName = da["@name"]
  projectAuth = da["xmi:Extension"]["eAnnotations"]["details"][1]["@value"]
  print(f"Leyendo {projectName} por {projectAuth}")
  def detectType(obj):
    typ = "Indefinido"
    if "@type" in obj.keys():
      typ = obj["@type"]
    elif "type" in obj.keys():
      typ = obj["type"]["@href"].split("//")[-1]
    return typ
  def readElement(element):

    def readOperation(element, operations):
      """Links a set of operations to its parent element"""
      for op in operations:
        o = Operation(name=op["@name"],visibility=op["@visibility"],xmi_id=op["@xmi:id"],parameters=[])
        if "ownedParameter" in op.keys():
          for p in op["ownedParameter"]: # TODO add an exceptions clause
            uni = True
            if type(p) is dict:
              if "@isUnique" in p.keys() and  p["@isUnique"] == "false":
                uni = False
              dir = ""
              if "@direction" in p.keys():
                dir = p["@direction"]
              par = Parameter(name=p["@name"],
                              xmi_id=p["@xmi:id"],
                              is_unique=uni,
                              direction=dir,
                              o_type=detectType(p))
              o.parameters.append(par)
        element.operations.append(o)

    def readAttribute(element, attributes, is_enum=False):
        """Links a set of attributes to its parent element"""
        for att in attributes:
          if is_enum:
            a = Attribute(name=att["@name"],
                          xmi_id=att["@xmi:id"],
                          visibility=att["@enumeration"],
                          o_type=detectType(att))
          else:
            a = Attribute(name=att["@name"],
                          xmi_id=att["@xmi:id"],
                          visibility=att["@visibility"],
                          o_type=detectType(att))

          element.attributes.append(a)

    e = UMLCLass(name=element["@name"], xmi_id=element["@xmi:id"], attributes=[], operations=[])
    if "ownedOperation" in element.keys():
      readOperation(e, element["ownedOperation"])
    if "ownedAttribute" in element.keys():
      readAttribute(e, element["ownedAttribute"])
    if "ownedLiteral" in element.keys():
      readAttribute(e, element["ownedLiteral"],is_enum=True)
    if "interfaceRealization" in element.keys():
      reali = readAssociation(element["interfaceRealization"], is_realization= True)
      relations.append(reali)
    id_lookup.append( [e.name,e.xmi_id])
    return e

  def readAssociation(asoc, is_usage= False, is_realization=False):

    def lookAggregation(terminal):
      agg = "parent"
      if "@aggregation" in terminal.keys():
        agg = terminal["@aggregation"]
      return agg

    def setRange(terminal):
      return (terminal["lowerValue"]["@value"],terminal["upperValue"]["@value"])

    if is_usage:
      asoc["@name"] = "USAGE"
    if is_realization:
      asoc["@name"] = "REALIZATION"
    nex = Association(name=asoc["@name"],
                      xmi_id=asoc["@xmi:id"],
                      nl_nexus=[],
                      id_nexus=[],
                      directed=False,
                      terminals = [])
    if is_usage or is_realization:
      nex.directed=True #first goes the client, then supplier
      nex.id_nexus= [asoc["@client"],asoc["@supplier"]]
    else:
      for terminal in asoc["ownedEnd"]:
          ter = Terminal(name=terminal["@name"],
                        xmi_id=terminal["@xmi:id"],
                        o_type=terminal["@type"],
                        aggregation=lookAggregation(terminal),
                        range=setRange(terminal))
          nex.terminals.append(ter)
          nex.nl_nexus.append(ter.name)
          nex.id_nexus.append(ter.xmi_id)

    id_lookup.append( [nex.name,nex.xmi_id])
    return nex

  for el in da["packagedElement"]:
    t = el["@xsi:type"]
    if t == "uml:Class":
      classes.append(readElement(el))
    elif t == "uml:Association":
      relations.append(readAssociation(el))
    elif t == "uml:Enumeration":
      classes.append(readElement(el))
    elif t == "uml:Interface":
      classes.append(readElement(el))
    elif t == "uml:Usage":
      relations.append(readAssociation(el,is_usage=True))
  return (classes, relations,id_lookup)

def interpreter(info, pdfInfo=""):
  def xmid_to_name(info,lookup,types=False):
    """Transforms al xmi:id iterations to its natural language name"""
    if types:
      for c in info[0]:
        for a in c.attributes:
          if a.o_type in lookup.keys():
            a.o_type = lookup[a.o_type]
        for o in c.operations:
          if len(o.parameters) >= 1:
            for p in o.parameters:
              if p.o_type in lookup.keys():
                p.o_type = lookup[p.o_type]

    else:
      for r in info[1]:
        if len(r.nl_nexus) < 1:
          for n in r.id_nexus:
            r.nl_nexus.append(lookup[n])
  def paragraph_from_class(uclass):
    """Generates a paragraph from a given class"""
    par = f"La clase {uclass.name} posee los atributos: "
    for a in uclass.attributes:
      par += f"{a.name} de visibilidad {a.visibility} que pertenece a la clase {a.o_type}, "

    par = par[:-2]+"."
    par_o = f"Adicionalmente, {uclass.name} posee las funciones: \n "
    for o in uclass.operations:
      par_o += f"{o.name}, que"
      if len(o.parameters) < 1:
        par_o += " no posee parámetros. \n "
      else:
        par_o += " posee los parámetros: "
        for p in o.parameters:
          if p.name != "returnParameter":
            par_o += f"{p.name} del tipo {p.o_type}, "
        par_o = par_o[:-2]+ ". La función es pública. \n "

    return par + "\n" + par_o

  def paragraph_from_relation(rel):
    """Generates a paragraph from a given relation"""
    par = "Existe una relación de "
    if rel.name == "REALIZATION" or rel.name == "USAGE":
      if rel.name == "REALIZATION":
        par += "realización "
      else :
        par += "uso "
      par += f"entre las clases {rel.nl_nexus[0]} y {rel.nl_nexus[1]} en la cual {rel.nl_nexus[0]} es cliente y {rel.nl_nexus[1]} es proveedor."
    else:
      par += f"asociación entre las clases {rel.nl_nexus[0]} y {rel.nl_nexus[1]}: "
      for t in rel.terminals:
        par += f"la terminal de {t.name} tiene un valor mínimo de {t.range[0]} y uno máximo de {t.range[1]} y es {t.aggregation} en la relación, "
      par = par[:-2]+"."
    return par
  script = []
  if pdfInfo != "":
    script += pdfInfo
  lookup = {l[1]: l[0] for l in info[2]}
  xmid_to_name(info,lookup)
  xmid_to_name(info,lookup,types=True)
  print("Generando información de lenguaje")
  c_paragraphs, r_paragraphs = [],[]
  for c in info[0]:
    c_paragraphs.append(paragraph_from_class(c))
  for r in info[1]:
    r_paragraphs.append(paragraph_from_relation(r))
  return script + c_paragraphs + r_paragraphs

def generateJSON(info):
  """Generate prelimnary JSON file with the code structure"""
  #for c in info[0]:
  pass

def generatePrompt(info):
  """Generate prompt for Azure LLM API"""
  def read_names(obj):
    return [o.name for o in obj]
  content = {}
  for c in info[0]:
    content[c.name] = read_names(c.attributes) + read_names(c.operations) + [1]
  m_ini  = "messages= [{'role':'system','content':{"
  print(m_ini  + str(content)[1:-1] + "}}]")
  return m_ini + str(content)[1:-1] + "}}]"

def generateFileFromLLM():
  """Function that takes a set of strings, calls the LLM API, and generates a .py file"""
  pass

def packCode():
  """Function that compresses the LLM generated file and sends it to the Extension"""
  pass

prompt = ""
def main():
    d, pdf_info = openFile("TicTacToe.xmi",pdfInfo="Requerimientos funcionales para TicTacToe.pdf")
    p = generatePrompt(filter(d))
    d = interpreter(filter(d),pdf_info)
    d = [l.replace("\n","") for l in d]
    for e in d:
      print(e)
    print(p)
    prompt = p

main()
