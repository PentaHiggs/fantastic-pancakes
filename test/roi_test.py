import tensorflow as tf
import numpy as np
from .testUtils import eval_cpu, assertArrayAlmostEqual
from layers.custom_layers import roi_pooling_layer

# RoiPoolingLayer needs an image attributes input to extract a scale factor from
# These tests assume the scaling is 1, so we use the following
dummy_img_attr = np.array([1., 1., 1.])


def createDiagFeatures(width=16, height=16, channels=1, dtype=np.float32,
        asNumpyArray=False, inverted=(False, False, False)):
    ''' Creates a tf.constant tensor with consecutively numbered values '''
    if inverted[0]:
        w = np.arange(width - 1, -1, -1, dtype=dtype)
    else:
        w = np.arange(width, dtype=dtype)
    if inverted[1]:
        h = np.arange(height - 1, -1, -1, dtype=dtype)
    else:
        h = np.arange(height, dtype=dtype)
    if inverted[2]:
        c = np.arange(channels - 1, -1, -1, dtype=dtype)
    else:
        c = np.arange(channels, dtype=dtype)

    out0 = w + width * h[:, np.newaxis]
    out = out0[:, :, np.newaxis] + width * height * c[np.newaxis, np.newaxis, :]
    if not asNumpyArray:
        return tf.constant(out, dtype=dtype)
    else:
        return out


# Quick shape references
# feature_in.shape = (height,width,channels)
# pooled_out.shape = (num_rois, pooled_h, pooled_w, channels)
# roi_list.shape   = (num_rois, 4) (the 4 dims are [x0, y0, x1, y1])


class shapesTest(tf.test.TestCase):

    def test_shape_A(self):
        regions = tf.constant([[0., 0., 2., 2.], [4., 6., 10., 10.]])
        feat_map = tf.random_normal((4, 5, 6))
        op = roi_pooling_layer(feat_map, dummy_img_attr, regions, 7, 8, 16)
        result = eval_cpu(op, self)
        self.assertEqual(result.shape, (2, 7, 8, 6),
                "expected %s, got %s" % (str((2, 7, 8, 4)), str(result.shape)))

    def test_shape_B(self):
        regions = tf.constant([[33., 109., 204., 19, ]])
        feat_map = createDiagFeatures(width=16, height=16, channels=1)
        op = roi_pooling_layer(feat_map, dummy_img_attr, regions, 2, 2, 16)
        result = eval_cpu(op, self)
        self.assertEqual(result.shape, (1, 2, 2, 1), "Got %s" % str(result.shape))


class singleRegionOutputTest(tf.test.TestCase):
    def single_roi_test_template(self, features, expectation):
        regions = tf.constant([[33., 19., 204., 109.]])
        op = roi_pooling_layer(features, dummy_img_attr, regions, 2, 2, 16)
        result = eval_cpu(op, self)
        self.assertEqual(result.shape, (1, 2, 2, 1), "Shape incorrect.  Expected %s,\
            but got %s" % (str((1, 2, 2, 1)), str(result.shape)))
        assertArrayAlmostEqual(self, result, expectation)

    def test_regular_input(self):
        features = createDiagFeatures(width=16, height=16, channels=1)
        expectation = [[[[71], [77]], [[119], [125]]]]
        self.single_roi_test_template(features, expectation)

    def test_horiz_inverted_input(self):
        features = createDiagFeatures(width=16, height=16, channels=1,
            inverted=(True, False, False))
        expectation = [[[[77], [71]], [[125], [119]]]]
        self.single_roi_test_template(features, expectation)

    def test_vert_inverted_input(self):
        features = createDiagFeatures(width=16, height=16, channels=1,
            inverted=(False, True, False))
        expectation = [[[[231], [237]], [[183], [189]]]]
        self.single_roi_test_template(features, expectation)

    def test_both_inverted_input(self):
        features = createDiagFeatures(width=16, height=16, channels=1,
            inverted=(True, True, False))
        expectation = [[[[237], [231]], [[189], [183]]]]
        self.single_roi_test_template(features, expectation)


def create_regions(xMin, xMax, yMin, yMax, nRegions):
    xs = np.random.random_sample(nRegions)
    xs = (xMax - xMin) * xs + xMin
    ys = np.random.random_sample(nRegions)
    ys = (yMax - yMin) * ys + yMin

    hs = np.random.random_sample(nRegions)
    hs = (yMax - yMin) * hs / 4
    ws = np.random.random_sample(nRegions)
    ws = (xMax - xMin) * ws / 4

    regions = [[x, y, min(x + w, xMax), min(y + h, yMax)] for x, y, h, w in zip(xs, ys, hs, ws)]
    return np.round(np.array(regions))


class roiGradientTest(tf.test.TestCase):
    def test_roi_gradient(self):
        with self.test_session():
            nBatches = 4
            nChannels = 8
            features_shape = [38, 50, nChannels]
            features = tf.random_normal(features_shape)
            regions = create_regions(0, features_shape[0],
                                     0, features_shape[1],
                                     nBatches)
            dummy_img_attr = tf.constant([1., 1., 1.])
            pooled_out_shape = [nBatches, 7, 7, nChannels]

            y = roi_pooling_layer(features, dummy_img_attr, regions, 7, 7, 2)
            error = tf.test.compute_gradient_error(features, features_shape, y,
                pooled_out_shape, delta=0.0001)
            self.assertAlmostEqual(error, 0., delta=.001)


if __name__ == '__main__':
    tf.test.main
