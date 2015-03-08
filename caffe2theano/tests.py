import conversion
import os
def printt(string):
	print "====== [ TESTING: %s ] ======" % string
	return "====== [ TESTING: %s ] ======\n" % string

def printe(string):
	print "====== [ ERROR: %s ] ======" % string
	return "====== [ ERROR: %s ] ======\n" % string
def prints(string):
	print '===== [ STATUS: %s ] ======' % string
	return '===== [ STATUS: %s ] ======\n' % string

def main(prototxt, caffemodel):
	test_string = ''
	test_string += printt('Accuracy of conversion. Caffe required.')
	model = None
	try:
		import caffe
		net = Caffe.Net(prototxt,caffemodel,caffe.TEST)
		test_string += printt('Accuracy of conversion - caffe parsing')
		model = conversion.convert(prototxt,caffemodel,caffe_parse=True)
		l2_distance = test_similarity(model,net)
		if l2_distance < 1e-7:
			prints('Accuracy of conversion - caffe parsing: Passed')
		else:
			prints('Accuracy of conversion - caffe parsing: Failed')

		del model
		test_string += printt('Accuracy of conversion - protobuf parsing')
		model = conversion.convert(prototxt,caffemodel,caffe_parse=False)
		l2_distance = test_similarity(model,net)
		if l2_distance < 1e-7:
			prints('Accuracy of conversion - protobuf parsing: Passed')
		else:
			prints('Accuracy of conversion - protobuf parsing: Failed')
	except:
		test_string += printe('Caffe was not found. Continuing...')

	test_string += printt('Serialization')
	if model is not None:
		model = conversion.convert(prototxt,caffemodel)
	success = test_serialization(model)
	if success:
		test_string += prints('Serialization: Passed')
	else:
		test_string += prints('Serialization: Failed')

	print '=====================================\n'*10
	print 'SUMMARY:'
	print test_string



def test_similarity(model, net):
	inp_shape= net.blobs['data'].data.shape
	random_mat = np.random.randn(*inp_shape).astype(theano.config.floatX) 
	tick = time.time()
	fprop = net.forward(**{net.inputs[0]:random_mat})
	print fprop[fprop.keys()[0]].shape
	tock = time.time()
	print 'time: %s' % str(tock - tick)
	tick = time.time()
	outlist = model.forward(random_mat)
	tock = time.time()
	print 'model forward'
	print 'time: %s' % str(tock - tick)
	# print fprop vs outlist
	print 'L2 distance between output of caffe and output of theano'
	print np.sum((fprop[fprop.keys()[0]][:,:,0,0] - outlist[0])**2)
	print 'Max absolute different between entries in caffe and entries in theano'
	print np.amax(np.abs(fprop[fprop.keys()[0]][:,:,0,0]-outlist[0]))

	return np.sum((fprop[fprop.keys()[0]][:,:,0,0] - outlist[0])**2)


def test_serialization(model):
	random_mat = np.random.randn(*model.input_layer.shape)
	print "outlist_1"
	outlist_1 = model.forward(random_mat)
	print "dumping..."
	dump(model, 'temp_test.lm')
	print "loading..."
	loaded_model = load('temp_test.lm')
	os.system('rm temp_test.lm')
	print "begin outlist 2"
	outlist_2 = loaded_model.forward(random_mat)

	for i in range(len(outlist_1)):
		print 'L2 Distance between outputs:'
		print np.sum((outlist_1[i] - outlist_2[i])**2)
		if np.sum((outlist_1[i] - outlist_2[i])**2) > 1e-7:
			return False
		print 'Max absolute difference between entries:'
		print np.amax(np.abs(outlist_1[i]-outlist_2[i]))

	return True

if __name__ == '__main__':
	main('data/VGG_ILSVRC_16_layers_deploy.prototxt', 'data/VGG_ISLVRC_16_layers.caffemodel')