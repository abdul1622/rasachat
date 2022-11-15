from flask import Flask,url_for,redirect,request,render_template,jsonify
from flask_restful import Api,Resource
import json
from bson.json_util import loads,dumps,default
from bson import ObjectId
from yaml import SafeLoader,FullLoader
import yaml
from ruamel.yaml import YAML,util,comments
import sys
from rasa.nlu.convert import convert_training_data


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app = Flask(__name__)
api = Api(app)
from pymongo import MongoClient

client = MongoClient('mongodb+srv://root:YmaXmz16j8AfLi94@cluster1.lcpgfzf.mongodb.net/?retryWrites=true&w=majority')
db = client['FirstDB']

# @app.route('/<name>')
def success(name):
    if name:
        # db.posts.insertOne({'sender':name})
        db.posts.insert({'sender':name})
    return render_template('home.html',name=name)


@app.route('/ha')
def print_db():
    all = db.posts.find()
    print(all)
    for i in all:
        print(i)
        for y in i:
            print(i[y])
    return render_template('home.html',name=all)

if __name__ == '__main__':
    app.run(debug=True)

class Create(Resource):

    def get(self):
        data = db.posts.find()
        lis = list(data)
        data = dumps(lis)
        data = loads(data)
        # data = loads(data)
        data = JSONEncoder().encode(data)
        return ({'details':data})
  
    def post(self):
        data_in = request.get_json()
        print(data_in)
        db.posts.insert(data_in)
        data = db.posts.insert(data_in)
        data = db.posts.find()
        lis = list(data)
        data = dumps(lis)
        data = loads(data)
        data = JSONEncoder().encode(data)
        return ({'data': data}), 201


class Edit(Resource):

    def get(self,id):
        print(id)
        id = ObjectId(id)
        data = db.posts.find_one({"_id":id})
        print(data)
        data = dumps(data)
        data = loads(data)
        data = JSONEncoder().encode(data)
        self.data = data
        return ({'details':data})
    
    def put(self,id):
        print(id)
        id = ObjectId(id)
        data_in = request.get_json()
        data = db.posts.update_one({"_id":id},{"$set":data_in})
        data = db.posts.find_one({"_id":id})
        print(data)
    
    def delete(self,id):
        print(id)
        id = ObjectId(id)
        db.posts.delete_one({"_id":id})

api.add_resource(Create, '/')
api.add_resource(Edit, '/edit/<string:id>')

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

                    

@app.route('/intent',methods=['POST'])
def create_intent():
    if request.method == 'POST':
        data = request.data
        data = json.loads(data)

        print(data)
        # print(data['intent'])
        # adding intent
        # with open('/home/user5/django/rasachat/data/nlu.yml','a') as nlu:
        #     nlu.write("\n\n- intent: {}\n  examples: |".format(data['intent']))
        #     for i in data['examples']:
        #         nlu.write("\n    - {}".format(i))

# adding domain
    # code = None
    # with open('/home/user5/django/rasachat/data/domain.yml') as file:
    #     yaml2 = YAML()
    #     config, ind, bsi = util.load_yaml_guess_indent(open('/home/user5/django/rasachat/data/domain.yml'))
    #     code = yaml.load(file,Loader=SafeLoader)
    #     yaml2.indent(sequence=ind, offset=bsi)
    #     yaml2.sort_key = False
    #     yaml2.preserve_quotes = True
    #     print(type(code))
    #     code['intents'].append(data['intent'])
    #     code['responses'][data['action']] = [{'text':data['action_text']}]
    #     print(code['responses'])

    # with open("/home/user5/django/rasachat/data/domain.yml", "w") as f:
    #     yaml2.indent(mapping=2, sequence=3, offset=1)
    #     yaml2.dump(code, f)

    # adding stories file
    with open('/home/user5/django/rasachat/data/stories.yml','a') as stories_file:
        stories_file.write('\n- story: {}\n  steps:\n'.format(data['story_head']))
        if data['stories']:
            for i in data['stories']:
                print(i)
                stories_file.write('  - intent: {}\n  - action: {}\n'.format(i['int'],i['act']))
        else:
            stories_file.write('  - intent: {}\n  - action: {}\n'.format(data['intent'],data['action']))
    return {'data':'success'}
