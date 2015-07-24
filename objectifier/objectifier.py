import json

# Import yaml if available
try:
    import yaml
except ImportError:
    yaml = None


try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

# ElementTree in 2.7 raises ElementTree.ParseError; 2.6 raises SyntaxError
try:
    ElementTree.ParseError
except AttributeError:
    ElementTree.ParseError = SyntaxError

def etree_list_items_all_have_same_tag(l):
    last_tag = None

    for x in l:
        if last_tag is not None and last_tag != x.tag:
            return False

        last_tag = x.tag

    return True


def arrayify_etree(tree):
    children = tree.getchildren()

    if len(children) == 0:
        return {tree.tag: tree.text}
    elif len(children) > 1 and etree_list_items_all_have_same_tag(children):
        l = [arrayify_etree(child)[child.tag] for child in children]
        return {tree.tag: {children[0].tag: l}}
    else:
        d = {}

        for child in children:
            d.update(arrayify_etree(child))

        return {tree.tag: d}


def arrayify_xml(xml_str):
    return arrayify_etree(ElementTree.fromstring(xml_str))

def is_list_of_2_element_tuples(input):
    if not isinstance(input, list):
        return False

    for item in input:
        if not isinstance(item, tuple) or len(item) != 2:
            return False

    return True

def parse_as_json(data):
    try:
        # Assume the data is JSON
        return json.loads(data)
    except ValueError:
        return None

def parse_as_yaml(data):
    if yaml is None:
        return None
    try:
        return yaml.load(data)
    except yaml.YAMLError:
        return None

def parse_as_xml(data):
    try:
        return arrayify_xml(data)
    except ElementTree.ParseError:
        return None

class Objectifier(object):
    def __init__(self, response_data):
        # self.response_data = None
        if type(response_data) == dict:
            self.response_data = response_data
            return
        if type(response_data) == list:
            if is_list_of_2_element_tuples(response_data):
                self.response_data = dict(response_data)
            else:
                self.response_data = response_data
            return
        if self._try_parsing(response_data, parse_as_json):
            return
        if self._try_parsing(response_data, parse_as_yaml):
            return
        if self._try_parsing(response_data, parse_as_xml):
            return
        self.response_data = response_data

    def _try_parsing(self, data, parser_function):
        try:
            self.response_data = parser_function(data)
        except:
            return False
        return self.response_data is not None


    @staticmethod
    def _objectify_if_needed(response_data):
        """
        Returns an objectifier object to wrap the provided response_data.
        """
        if hasattr(response_data, 'pop'): # In other words, if this is a list
            return Objectifier(response_data)
        return response_data

    def __dir__(self):
        try:
            return self.response_data.keys()
        except AttributeError:
            return []

    def __repr__(self):
        try:
            return "<Objectifier#dict {0}>".format(" ".join(["%s=%s" % (k, type(v).__name__)
                for k, v in self.response_data.iteritems()]))
        except AttributeError:
            try:
                return "<Objectifier#list elements:{0}>".format(len(self.response_data))
            except TypeError:
                return self.response_data

    def __contains__(self, k):
        return k in self.response_data

    def __len__(self):
        return len(self.response_data)

    def __iter__(self):
        """
        Provides iteration functionality for the wrapped object.
        """
        try:
            for k, v in self.response_data.iteritems():
                yield (k, Objectifier._objectify_if_needed(v))
        except AttributeError:
            try:
                for i in self.response_data:
                    yield Objectifier._objectify_if_needed(i)
            except TypeError:
                raise StopIteration

    def __getitem__(self, k):
        try:
            return Objectifier._objectify_if_needed(self.response_data[k])
        except TypeError:
            return None

    def __getattr__(self, k):
        if k in self.response_data:
            return Objectifier._objectify_if_needed(self.response_data[k])
        return None


