

def set_params(theano_layer, net, layer_params):
	'''
	theano_layer is a theano layer
	net is the caffe net
	layer_params is the layer params
	'''
	if len(theano_layer.get_params())== 0:
		return # no params to set
	else:
		if layer_params['type'] == 'CONVOLUTION' or layer_params['type'] == 'Convolution':
			if cuda==True:
				set_cuda_conv_params(theano_layer, net, layer_params)
			else:
				set_conv_params(theano_layer, net, layer_params)
		elif layer_params['type'] == 'INNER_PRODUCT' or layer_params['type'] == 'InnerProduct':
			set_ip_params(theano_layer, net, layer_params)
		else:
			print "not a valid layer to set params to (what happened??) %s" % layer_params['type']

# def set_conv_params(theano_layer, net, layer_params):
# 	name = layer_params['name']
# 	W = net.params[name][0].data
# 	b = net.params[name][1].data
# 	# b needs to just be the last index
# 	b = b[0,0,0,:]
# 	# W needs to be fixed
# 	W = W[:,:,::-1,::-1]
# 	theano_layer.W.set_value(W.astype(theano.config.floatX))
# 	theano_layer.b.set_value(b.astype(theano.config.floatX))

# def set_cuda_conv_params(theano_layer, net, layer_params):
# 	name = layer_params['name']
# 	W = net.params[name][0].data
# 	b = net.params[name][1].data
# 	# b needs to just be the last index
# 	b = b[0,0,0,:]
# 	# W needs to be reshaped into n_features(from prev layer), size, size, n_filters
# 	theano_layer.W.set_value(W.astype(theano.config.floatX))
# 	theano_layer.b.set_value(b.astype(theano.config.floatX))

# def set_ip_params(theano_layer, net, layer_params):
# 	name = layer_params['name']
# 	W = net.params[name][0].data
# 	b = net.params[name][1].data

# 	# W needs to just be the last 2, shuffled
# 	W = W[0,0,:,:].T
# 	# b needs to just be the last index
# 	b = b[0,0,0,:]
# 	theano_layer.W.set_value(W.astype(theano.config.floatX))
# 	theano_layer.b.set_value(b.astype(theano.config.floatX))


def parse_layer(layer, last_layer):
	'''
	returns the correct layer given the param dict
	'''
	if layer['type'] == 'CONVOLUTION' or layer['type'] == 'Convolution':
		if cuda==True:
			return cuda_conv_layer_from_params(layer, last_layer)
		else:
			return conv_layer_from_params(layer, last_layer)
	elif layer['type'] == 'RELU' or layer['type'] == 'ReLU':
		return relu_layer_from_params(layer, last_layer)
	elif layer['type'] == 'POOLING' or layer['type'] == 'Pooling':
		if cuda==True:
			return cuda_pooling_layer_from_params(layer, last_layer)
		else:
			return pooling_layer_from_params(layer, last_layer)
	elif layer['type'] == 'INNER_PRODUCT' or layer['type'] == 'InnerProduct':
		return ip_layer_from_params(layer, last_layer)
	elif layer['type'] == 'DROPOUT' or layer['type'] == 'Dropout':
		return dropout_layer_from_params(layer, last_layer)
	elif layer['type'] == 'SOFTMAX' or layer['type'] == 'Softmax':
		return softmax_layer_from_params(layer, last_layer)
	elif layer['type'] == 'LRN':
		return lrn_layer_from_params(layer, last_layer)
	else:
		print 'not a valid layer: %s' % layer['type']
		return -1

def lrn_layer_from_params(layer, last_layer):
	# set params
	alpha = float(layer['alpha'])
	beta = float(layer['beta'])
	n = int(layer['local_size'])

	lrn = extra_layers.CaffeLocalResponseNormalization2DLayer(last_layer, alpha=alpha, beta=beta, n=n)
	return lrn

def cuda_conv_layer_from_params(layer, last_layer):
	num_filters = int(layer['num_output'])
	filter_size = (int(layer['kernel_size']),int(layer['kernel_size'])) #only suppose square filters
	strides = (int(layer['stride']),int(layer['stride'])) # can only suport square strides anyways
	## border mode is wierd...
	border_mode = None
	pad = int(layer['pad'])
	nonlinearity=nonlinearities.identity
	groups= int(layer['group'])
			
	conv = extra_convnet_layers.CaffeConv2DCCLayer(last_layer, groups=groups, num_filters=num_filters,filter_size=filter_size, strides=strides, border_mode=border_mode, pad=pad, nonlinearity=nonlinearity)
	return conv

def conv_layer_from_params(layer, last_layer):
	# theano's conv only allows for certain padding, not arbitrary. not sure how it will work if same border mode is not true.
	if int(layer['kernel_size']) - (int(layer['pad']) * 2 ) == 1:
		print "using same convolutions, this should be correct"
		border_mode = 'same'
	else:
		print "using valid border mode, this should work but who knows"
		border_mode='valid'

	num_filters = int(layer['num_output'])
	filter_size = (int(layer['kernel_size']), int(layer['kernel_size'])) # must be a tuple
	strides = (int(layer['stride']),int(layer['stride'])) # can only suport square strides anyways
	group = int(layer['group'])
	## border mode is wierd...
	
	nonlinearity=nonlinearities.identity

	if group > 1:
		conv = extra_convnet_layers.CaffeConv2DLayer(last_layer, group=group,num_filters=num_filters, filter_size=filter_size, strides=strides, border_mode=border_mode, nonlinearity=nonlinearity)
	else:
		conv = layers.Conv2DLayer(last_layer, num_filters=num_filters, filter_size=filter_size, strides=strides, border_mode=border_mode, nonlinearity=nonlinearity)
	return conv

def relu_layer_from_params(layer, last_layer):
	return extra_layers.ReluLayer(last_layer)

def pooling_layer_from_params(layer, last_layer):
	ds=(int(layer['kernel_size']),int(layer['kernel_size'])) #caffe only does square kernels
	strides = (int(layer['stride']), int(layer['stride']))

	if strides[0] != ds[0]:
		pool = extra_layers.CaffeMaxPool2DLayer(last_layer,ds=ds, strides=strides)
	else:
		pool = layers.MaxPool2DLayer(last_layer, ds=ds) # ignore border is set to False, maybe look into how caffe does borders if the strides don't work perfectly
	return pool

def cuda_pooling_layer_from_params(layer, last_layer):
	ds = (int(layer['kernel_size']),int(layer['kernel_size'])) # cuda only supports square anyways
	strides = (int(layer['stride']), int(layer['stride'])) #only square strides as well

	pool = cuda_convnet.MaxPool2DCCLayer(last_layer, ds=ds, strides=strides)
	return pool

def ip_layer_from_params(layer, last_layer):
	num_units=int(layer['num_output'])
	nonlinearity=nonlinearities.identity
	if cuda==False:
		dense = layers.DenseLayer(last_layer, num_units=num_units, nonlinearity=nonlinearity)
	else:
		dense = layers.DenseLayer(last_layer, num_units=num_units, nonlinearity=nonlinearity)
	return dense

def dropout_layer_from_params(layer, last_layer):
	'''
	TODO: IMPLEMENT THIS. currently only using this script for forward passes, so this can be a complete identity
	but in the future maybe i'll want to finetune, so this would need to be implemented.
	'''
	return extra_layers.IdentityLayer(last_layer)

def softmax_layer_from_params(layer, last_layer):
	return extra_layers.SoftmaxLayer(last_layer)



