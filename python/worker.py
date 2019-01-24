import json
from io import BytesIO
from traceback import print_exc
from progress import setCallback, initialETA
from imageProcess import clean

def context(): pass
context.root = None
context.getFile = lambda size: BytesIO(context.sharedView[:size])

def begin(root, nodes=[], setAllCallback=True):
  context.root = root
  root.nodes = []
  for n in nodes:
    root.append(n)
  if setAllCallback:
    setCallback(root, onProgress)
  else:
    root.setCallback(onProgress)
  initialETA(root)
  return root

def onProgress(node, kwargs={}):
  res = {
    'eta': context.root.eta,
    'gone': context.root.gone,
    'total': context.root.total
  }
  res.update(kwargs)
  if hasattr(node, 'name'):
    res['stage'] = node.name
    res['stageProgress'] = node.gone
    res['stageTotal'] = node.total
  context.notifier.send(res)

def enhance(f):
  def g(*args):
    try:
      result = f(*args)
      code = 200
    except Exception as e:
      print('错误内容=='+str(e))
      print_exc()
      result = 'Fail'
      code = 400
    finally:
      clean()
    return (json.dumps({'result': result}, ensure_ascii=False), code)
  return g

def setup(mm, routesDef):
  global routes
  routes = routesDef
  mm.seek(0)
  context.sharedView = memoryview(mm)
  context.shared = mm

def worker(taskIn, taskOut, notifier, stopEvent):
  context.notifier = notifier
  context.stopFlag = stopEvent
  while True:
    task = taskIn.recv()
    stopEvent.clear()
    result = routes[task[0]](*task[1:])
    taskOut.send(result)