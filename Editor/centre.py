from flask import (
    Blueprint, request, jsonify
)

bp = Blueprint('centre', __name__)

ops = []
'''
   type     index  text  last_rev  user
ADD DELETE,  int,  str     int,     User 
'''
@bp.route('/send/op', methods = ['POST'])
def send_op():
    usr = request.form['user']
    typ = request.form['type']
    ind = int(request.form['index'])
    rev = int(request.form['last_rev'])
    print(f"RECEIVED: send_op(): user={usr}, type={typ}, index={ind}, last_rev={rev}")
    if typ != 'ADD' and typ != 'DELETE':
        print(f"ERROR: send_op(): invalid type of operation type={typ}")
        return jsonify({'result': 'invalid_type'})
    if typ =='ADD' and ('text' not in request.form or len(request.form['text']) != 1) :
        print(f"ERROR: send_op(): invalid text of operation")
        return jsonify({'result': 'invalid_text'})

    for i in range(rev + 1, len(ops)):
        op = ops[i]
        if op['type'] == 'ADD':
            if ind >= op['index']:
                ind += 1
        elif op['type'] == 'DELETE':
            if ind < op['index']:
                ind -= 1
    ops.append({'review': len(ops)+1, 'type': typ, 'index': ind, 'last_rev': rev, 'user': usr})
    if typ == 'ADD':
        ops[-1]['text'] = request.form['text']
    return jsonify({'review': ops[-1]['review'], 'result': 'success'})

@bp.route('/get/newops', methods = ['POST'])
def get_newops():
    last_rev = int(request.form['last_rev'])
    last_ops = {}
    for i, op in enumerate(ops[last_rev:]):
        last_ops[i] = op
    return jsonify(last_ops)
