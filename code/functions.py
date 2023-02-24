###################### -------------------------------------------------------- ######################
###################### -------------------- User functions -------------------- ######################
###################### -------------------------------------------------------- ######################

import sys
import CSF
import timeit
import laspy
import jakteristics as jak
import numpy as np
from scipy import optimize as opt
from scipy.cluster import hierarchy as sch
from scipy.spatial import distance_matrix
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

#-----------------------------------------------------------------------------------------------------------------------------------
# voxelate
#----------------------------------------------------------------------------------------------------------------------------------------                  


def voxelate(cloud, resolution_xy, resolution_z, n_digits = 5, X_field = 0, Y_field = 1, Z_field = 2, with_n_points = True):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    Function used to voxelate point clouds. It allows to use a different resolution for (z),
    but (x, y) will always share the same resolution. It also allows to revert the process,
    by creating a unique code for each point in the point cloud, thus voxelated cloud can be 
    seamlessly reverted to the original point cloud.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    cloud: numpy array. the point cloud to be voxelated. It is expected to have X, Y, Z fields.
    resolution_xy: float. (x, y) voxel resolution.
    resolution_z: float. (z) voxel resolution.
    n_digits: int. default value: 5. Number of digits dedicated to each coordinate ((x), (y) or (z))
    during the generation of each point code. If the cloud is really large, it can be advisable
    to increase n_digits.
    X_field: int. default value: 0. Index at which (x) coordinate is stored.
    Y_field: int. default value: 1. Index at which (y) coordinate is stored.
    Z_field: int. default value: 2. Index at which (z) coordinate is stored.
    with_n_points: boolean. default value: True. If True, output voxelated cloud will have a field 
    including the number of points that each voxel contains.

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    voxelated_cloud: numpy array. The voxelated cloud. It consists of 3 columns, each with
    (x), (y) and (z) coordinates, and an optional 4th column having the number of points included
    in each voxel if with_n_points = True. 
    vox_to_cloud_ind: numpy array. Vector containing the indexes to revert to the original point cloud
    from the voxelated cloud.  
    cloud_to_vox_ind: numpy array. Vector containing the indexes to directly go from the original point cloud
    to the voxelated cloud.  
    '''
    
    t = timeit.default_timer()
    
    # The coordinate minima
    cloud_min = np.min(cloud[:,[X_field, Y_field, Z_field]], axis = 0)
  
    # Substraction of the coordinates
    cloud[:, X_field] = cloud[:, X_field] - cloud_min[X_field];
    cloud[:, Y_field] = cloud[:, Y_field] - cloud_min[Y_field];
    cloud[:, Z_field] = cloud[:, Z_field] - cloud_min[Z_field];
    
    elapsed = timeit.default_timer() - t
    print('      -Voxelization')
    print('        ','Voxel resolution:',"{:.2f}".format(resolution_xy),'x',"{:.2f}".format(resolution_xy),'x',"{:.2f}".format(resolution_z),'m')
    print('        ',"%.2f" % elapsed,'s: escaling and translading')
    
    # Generation of 'pixel code'. It provides each point with an unique identifier. 
    code = np.floor(cloud[:, Z_field] / resolution_z) * 10 ** (n_digits * 2) + np.floor(cloud[:, Y_field] / resolution_xy) * 10 ** n_digits + np.floor(cloud[:, X_field] / resolution_xy)
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: encoding')
    
    # Vector that contains the ordered code. It will be used to sort the code to then sort the cloud.
    vox_order_ind = np.argsort(code)
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: 1st sorting')
    
    # Vector that contains the indexes of said code. It will be used to restore the order of points within the original cloud.
    vox_order_ind_inverse = np.argsort(vox_order_ind)
    
    # Sorted code.
    code = code[vox_order_ind]
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: 2nd sorting')
    
    # Unique values of said 'pixel code':
    # unique_code: Unique values. They contain codified coordinates of which will later be the voxel centroids. 
    # vox_first_point_id. Index corresponding to the point of each voxel that corresponds to the first point, among those in the same voxel, in the original cloud.
    # inverse_id: Indexes that allow to revert the voxelization. 
    # vox_points: Number of points in each voxel
    unique_code, vox_first_point_id, inverse_id, vox_points = np.unique(code, return_index = True, return_inverse = True, return_counts = True)
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: extracting uniques values')
    
    # Indexes that directly associate each voxel to its corresponding points in the original cloud (unordered)
    vox_to_cloud_ind = inverse_id[vox_order_ind_inverse]
    
    # Indexes that directly associate each point in the original, unordered cloud to its corresponding voxel
    cloud_to_vox_ind = vox_order_ind[vox_first_point_id]
    
    # Empty array to be filled with voxel coordinates
    voxelated_cloud = np.zeros((np.size(unique_code, 0), 3))
    
    # Each coordinate 'pixel code'. They will then be transformed into coordinates
    z_code = np.floor(unique_code / 10 ** (n_digits * 2))
    y_code = np.floor((unique_code - z_code * 10 ** (n_digits * 2)) / 10 ** n_digits)
    x_code = unique_code - z_code * 10 ** (n_digits * 2) - y_code * 10 ** n_digits 
    
    voxelated_cloud[:, X_field] = x_code
    voxelated_cloud[:, Y_field] = y_code
    voxelated_cloud[:, Z_field] = z_code 
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: decomposing code')
    
    # Transformation of x, z, y codes into X, Y, X voxel coordinates, by scaling, translating and centering. 
    voxelated_cloud[:, Z_field] = voxelated_cloud[:, Z_field] * resolution_z  + cloud_min[Z_field] + resolution_z  / 2
    voxelated_cloud[:, Y_field] = voxelated_cloud[:, Y_field] * resolution_xy + cloud_min[Y_field] + resolution_xy / 2
    voxelated_cloud[:, X_field] = voxelated_cloud[:, X_field] * resolution_xy + cloud_min[X_field] + resolution_xy / 2
    
    # Boolean parameter that includes or not a 4th column with the number of points in each voxel
    if with_n_points == True:
        voxelated_cloud = np.append(voxelated_cloud, vox_points[:, np.newaxis], axis = 1)
    
    elapsed = timeit.default_timer() - t
    print('        ',"%.2f" % elapsed,'s: reescaling and translading back')
    
    print('        ',"{:.2f}".format(vox_to_cloud_ind.shape[0] / 1000000),'million points ->',"{:.2f}".format(cloud_to_vox_ind.shape[0] / 1000000),'million voxels')
    print('        ','Voxels account for',"{:.2f}".format(cloud_to_vox_ind.shape[0] * 100 / vox_to_cloud_ind.shape[0]),'% of original points')


    cloud[:, X_field] = cloud[:, X_field] + cloud_min[X_field];
    cloud[:, Y_field] = cloud[:, Y_field] + cloud_min[Y_field];
    cloud[:, Z_field] = cloud[:, Z_field] + cloud_min[Z_field];

    # Output. It consists in 3 arrays: - voxelated cloud (X, Y, Z, n_points) - voxel to original cloud indexes - original to voxel cloud indexes.
    return voxelated_cloud, vox_to_cloud_ind, cloud_to_vox_ind



#-----------------------------------------------------------------------------------------------------------------------------------
# verticality_clustering
#-----------------------------------------------------------------------------------------------------------------------------------

def verticality_clustering(stripe, vert_scale, vert_treshold, eps, n_points, resolution_xy, resolution_z, n_digits):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function is to be used internally by verticality_clustering_iteration.
    The intended use of this function is to accept a stripe as an input, defined this as a subset of 
    the original cloud delimited by a lower height and an upper height, which will narrow down a region 
    where it is expected to only be stems. Then it will voxelate those points and compute the verticality
    via compute_features() from jakteristics. It will filter points based on their verticality value, 
    voxelate again and then cluster the remaining points. Those are expected to belong to stems.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    stripe: numpy array. The point cloud containing the stripe. It is expected to have X, Y, Z fields.
    vert_scale: float. Scale to be used during verticality computation to define a neighbourhood around 
    a given point. Verticality will be computed from the structure tensor of said neighbourhood via 
    eigendecomposition.
    vert_threshold: float. Minimum verticality value associated to a point to consider it as part of a stem.
    eps: float. Refer to DBSCAN documentation.
    n_points: int. Minimum number of points in a cluster for it to be considered as a potential stem.
    resolution_xy: float. (x, y) voxel resolution.
    resolution_z: float. (z) voxel resolution.
    n_digits: int. default value: 5. Number of digits dedicated to each coordinate ((x), (y) or (z))
    during the generation of each point code. If the cloud is really large, it can be advisable
    to increase n_digits.

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    clust_stripe: numpy array. Point cloud containing the points from the stripe that are considered as stems. 
    It consists of 4 columns: (x), (y) and (z) coordinates, and a 4th column containing the cluster ID of the 
    cluster that each point belongs to.
    t1: float. Time spent.
    '''
    
    t = timeit.default_timer()
    print(" -Computing verticality...")
    
    # Call to 'voxelate' function to voxelate the cloud.
    voxelated_stripe, vox_to_stripe_ind, stripe_to_vox_ind = voxelate(stripe, resolution_xy, resolution_z, n_digits,with_n_points = False)
    
    # Computation of verticality values associated to voxels using 'compute_features' function. It needs a vicinity radius, provided by 'vert_scale'.
    vert_values = jak.compute_features(voxelated_stripe, search_radius = vert_scale, feature_names = ["verticality"])

    elapsed = timeit.default_timer() - t
    print("   %.2f" % elapsed,'s')
    t1 = elapsed
    
    # Verticality values are appended to the ORIGINAL cloud, using voxel-to-original-cloud indexes.
    vert_stripe = np.append(stripe, vert_values[vox_to_stripe_ind], axis = 1)
    
    # Filtering of points that were in voxels whose verticality value is under the threshold. Output is a filtered cloud.
    filt_stripe = vert_stripe[vert_stripe[:, -1] > vert_treshold]
    
    t = timeit.default_timer()
    print(" -Clustering...")
    
    # The filtered cloud is voxelated.
    vox_filt_stripe, vox_to_filt_stripe_ind, filt_stripe_to_vox_ind = voxelate(filt_stripe, resolution_xy, resolution_z, n_digits, with_n_points = False)    
    
    # Clusterization of the voxelated cloud obtained from the filtered cloud. 
    # 'eps': The maximum distance between two samples for one to be considered as in the neighborhood of the other. 
    #        This is not a maximum bound on the distances of points within a cluster. 
    # min samples: The number of samples (or total weight) in a neighborhood for a point to be considered as a core point. 
    #              This includes the point itself.
    clustering = DBSCAN(eps = eps, min_samples = 2).fit(vox_filt_stripe)
    
    elapsed = timeit.default_timer() - t
    print("   %.2f" % elapsed,'s')
    t1 = elapsed + t1
    
    t = timeit.default_timer()
    print(" -Extracting 'candidate' stems...")
    
    # Cluster labels are appended to the FILTERED cloud. They map each point to the cluster they belong to, according to the clustering algorithm.
    vox_filt_lab_stripe = np.append(filt_stripe, np.expand_dims(clustering.labels_[vox_to_filt_stripe_ind], axis = 1), axis = 1)
    
    # Set of all cluster labels and their cardinality: cluster_id = {1,...,K}, K = 'number of clusters'.
    cluster_id, K = np.unique(clustering.labels_, return_counts = True)
    
    # Filtering of labels associated only to clusters that contain a minimum number of points.
    large_clusters = cluster_id[K > n_points]
    
    # ID = -1 is always created by DBSCAN() to include points that were not included in any cluster.
    large_clusters = large_clusters[large_clusters != -1]
    
    # Removing the points that are not in valid clusters.       
    clust_stripe = vox_filt_lab_stripe[np.isin(vox_filt_lab_stripe[:, -1], large_clusters)]
    
    n_clusters = large_clusters.shape[0]
    
    elapsed = timeit.default_timer() - t
    print("   %.2f" % elapsed,'s')
    t1 = elapsed + t1
    print("   %.2f" % t1, 's per iteration')
    print("   ", n_clusters, " clusters")
    return clust_stripe, t1



#-----------------------------------------------------------------------------------------------------------------------------------
# verticality_clustering_iteration
#----------------------------------------------------------------------------------------------------------------------------------------                  

def verticality_clustering_iteration(stripe, scale,vert_treshold, eps_dbscan, n_points, n_iter, resolution_xy, resolution_z, n_digits):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function implements a for loop that iteratively calls verticality_clustering_iteration, 
    'peeling off' the stems.


    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    stripe: numpy array. The point cloud containing the stripe. It is expected to have X, Y, Z fields.
    vert_scale: float. Scale to be used during verticality computation to define a neighbourhood around 
    a given point. Verticality will be computed from the structure tensor of said neighbourhood via 
    eigendecomposition.
    vert_threshold: float. Minimum verticality value associated to a point to consider it as part of a stem.
    eps: float. Refer to DBSCAN documentation.
    n_points: int. Minimum number of points in a cluster for it to be considered as a potential stem.
    n_iter: integer. Number of iterations of 'peeling'.
    resolution_xy: float. (x, y) voxel resolution.
    resolution_z: float. (z) voxel resolution.
    n_digits: int. default value: 5. Number of digits dedicated to each coordinate ((x), (y) or (z))
    during the generation of each point code. If the cloud is really large, it can be advisable
    to increase n_digits.


    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    clust_stripe: numpy array. Point cloud containing the points from the stripe that are considered as stems. 
    It consists of 4 columns: (x), (y) and (z) coordinates, and a 4th column containing the cluster ID of the 
    cluster that each point belongs to.
    '''
    
    # This first if loop is just a fix that allows to compute everything ignoring verticality.
    # It should be addressed as it currently computes verticality when n_iter = 0 and that should
    # not happen (although, in practice, n_iter should never be 0).
    # It does not provide wrong results but it slows down the process needlessly.
    if n_iter == 0:
        n_iter = 1
        vert_treshold = 0
    
    # Basically, use verticality_clustering as many times as defined by n_iter
    for i in np.arange(n_iter):
        print("Iteration number",i + 1,"out of", n_iter)
        if i == 0:
            total_t = 0
            aux_stripe = stripe
        else:
            aux_stripe = clust_stripe
        clust_stripe, t = verticality_clustering(aux_stripe, scale, vert_treshold, eps_dbscan, n_points, resolution_xy, resolution_z, n_digits)
        total_t = total_t + t
    print("Final:")            
    print("%.2f" % total_t, 's in total (whole process)')   
    return clust_stripe
 
    

#-----------------------------------------------------------------------------------------------------------------------------------
# compute_axes
#-----------------------------------------------------------------------------------------------------------------------------------

def compute_axes(voxelated_cloud, clust_stripe, min_points, h_range, d_max, X_field, Y_field, Z_field, Z0_field, tree_id_field):
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    Function used inside individualize_trees during tree individualization process. 
    It identifies tree axes.
    It expects a  voxelated version of the point cloud and a filtered (based on the 
    verticality clustering process) stripe as input, so that it only contains (hopefully) stems.
    Those stems are isolated and enumerated, and then, their axes are identified using PCA 
    (PCA1 direction). This allows to group points based on their distance to those axes, 
    thus assigning each point to a tree. 
    It requires a normalized cloud in order to function properly; see cloud normalization appendix.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    voxelated_cloud: numpy array. the voxelated point cloud containing the forest plot. It is expected to have X, Y, Z and/or Z0 fields.
    clust_stripe: numpy array. The point cloud containing the clusterized stripe from verticality_clustering_iteration. 
    It is expected to have X, Y, Z and cluster ID fields.
    d_max: float. Points that are closer than d_max to an axis are assigned to that axis.
    h_range: float. only stems where points extend vertically throughout a range as tall as defined by h_range are considered
    min_points: int. Minimum number of points in a cluster for it to be considered as a potential stem.
    tree height.
    X_field: int. default value: 0. Index at which (x) coordinates are stored.
    Y_field: int. default value: 1. Index at which (y) coordinates are stored.
    Z_field: int. default value: 2. Index at which (z) coordinates are stored.
    Z0_field: int. default value: 3. Index at which (z0) coordinates are stored. 
    tree_id_field: int. default value: 4. Index at which cluster ID is stored. 

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    detected_trees: numpy array. Matrix with as many rows as trees, containing a description of each 
    individualized tree. It stores the following values: tree ID, PCA1 X value, PCA1 Y value, PCA1 Z value,
    stem centroid X value, stem centroid Y value, stem centroid Z value, height difference of stem centroid (z - z0),
    axis vertical deviation.
    dist_to_axis: numpy array. Matrix containing the distance from each point to the closest axis.
    tree_id_vector: numpy array. Vector containing the tree IDs. 
    '''
    # Empty vectors that will store final outputs: - distance from each point to closest axis - ID of the corresponding tree (the tree that the point belongs to).
    dist_to_axis = np.zeros((np.size(voxelated_cloud, 0))) + 100000 # distance to the closest axis
    tree_id_vector = np.zeros((np.size(voxelated_cloud, 0))) + 100000 # tree ID of closest axis
   
    # Set of all possible trees (trunks at this stage) and number of points associated to each:
    unique_values, n = np.unique(clust_stripe[:, tree_id_field], return_counts = True) 
   
    # Filtering of possible trees that do not contain enough points to be considered.
    filt_unique_values = unique_values[n > min_points]
   
    # Final number of trees (could be very well named tree_set, to be considered)
    n_values = np.size(filt_unique_values)
   
    # Empty array to be filled with several descriptors of the trees. In the following order:
    # tree ID | PCA1 X value | PCA1 Y value | PCA1 Z value | trunk centroid X value | trunk centroid Y value | trunk centroid Z value | height difference | 
    # It has as many rows as trees are.
   
    detected_trees = np.zeros((np.size(filt_unique_values, 0), 9))
    
    # Auxiliar index used to display progress information.
    ind = 0 
   
    # First loop: It goes over each tree (still stems) except for the first entry, which maps to noise (this entry is generated by DBSCAN during clustering).
    for i in filt_unique_values:

        # Isolation of stems: stem_i only contains points associated to 1 tree.
        stem_i = clust_stripe[clust_stripe[:, tree_id_field] == i][:, [X_field, Y_field, Z_field]]
        
        # Z and Z0 mean heights of points in a given tree
        z_z0 = np.average(clust_stripe[clust_stripe[:, tree_id_field] == i][:,[Z_field, Z0_field]], axis = 0)
         
        # Difference between Z and Z0 mean heights
        diff_z_z0 = z_z0[0] - z_z0[1]
             
        # Second loop: only stems where points extend vertically throughout its whole range are considered. 
        if np.ptp(stem_i[:, Z_field]) > (h_range):
                
            # PCA and centroid computation.
            pca_out = PCA(n_components = 3)
            pca_out.fit(stem_i)
            centroid = np.mean(stem_i, 0)
            
            # Values are stored in tree vector
            detected_trees[ind, 0] = i # tree ID
            detected_trees[ind, 1:4] = pca_out.components_[0, :] # PCA1 X value | PCA1 Y value | PCA1 Z value
            detected_trees[ind, 4:7] = centroid # stem centroid X value | stem centroid Y value | stem centroid Z value
            detected_trees[ind, 7] = diff_z_z0 # Height difference
            detected_trees[ind, 8] = np.abs(np.arctan(np.sqrt(detected_trees[ind, 1] ** 2 + detected_trees[ind, 2] ** 2) / detected_trees[ind, 3]) * 180 / np.pi)
           
            ind = ind + 1 
            sys.stdout.write("\r%d%%" % np.float64((n_values - ind) * 100 / n_values))
            sys.stdout.flush()            
   
            # Coordinate transformation from original to PCA. Done for EVERY point of the original cloud from the PCA of a SINGLE stem.
            cloud_pca_coords = pca_out.transform(voxelated_cloud[:, [X_field, Y_field, Z_field]])
       
            # Distance from every point in the new coordinate system to the axes. 
            # It is directly computed from the cuadratic component of PC2 and PC3 
            axis_dist = np.hypot(cloud_pca_coords[:, 1], cloud_pca_coords[:, 2])
            
            # Points that are closer than d_max to an axis are assigned to that axis.
            # Also, if a point is closer to an axis than it was to previous axes, accounting for points 
            # that were previously assigned to some other axis in previous iterations, it is assigned
            # to the new, closer axis. Distance to the axis is stored as well
            valid_points = (axis_dist < d_max) & ((axis_dist - dist_to_axis) < 0)
            tree_id_vector[valid_points] = i
            dist_to_axis[valid_points] = axis_dist[valid_points]
            
    return(detected_trees, dist_to_axis, tree_id_vector)



#-----------------------------------------------------------------------------------------------------------------------------------
# compute_heights
#-----------------------------------------------------------------------------------------------------------------------------------

def compute_heights(voxelated_cloud, detected_trees, dist_to_axis, tree_id_vector, d, max_dev, resolution_heights, n_digits, X_field, Y_field, Z_field, Z0_field):
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    Function used inside individualize_trees during tree individualization process. 
    It measures tree heights. The function creates a large-resolution voxel cloud to
    and filters voxels containing few points. This has the purpose to discard any outlier 
    point that might be over the trees, to then identify the highest point within the 
    remaining voxels. 
    
    It requires a normalized cloud in order to function properly; see cloud normalization appendix.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    voxelated_cloud: numpy array. the voxelated point cloud containing the forest plot. It is expected to have X, Y, Z and/or Z0 fields.
    detected_trees: numpy array. See compute_axes.
    dist_to_axis: numpy array. See compute_axes.
    tree_id_vector: numpy array. See compute_axes.
    d: float. Points within this distance from tree axis will be considered as potential points to define
    tree height.
    eps: float. Refer to DBSCAN documentation.
    max_dev: float. Maximum degree of vertical deviation of a tree axis to consider its tree height measurement as valid.
    n_digits: int. default value: 5. Number of digits dedicated to each coordinate ((x), (y) or (z))
    during the generation of each point code. If the cloud is really large, it can be advisable
    to increase n_digits.
    resolution_heights: float. default value: 0.3. Resolution used for voxelization.
    X_field: int. default value: 0. Index at which (x) coordinates are stored.
    Y_field: int. default value: 1. Index at which (y) coordinates are stored.
    Z_field: int. default value: 2. Index at which (z) coordinates are stored.
    Z0_field: int. default value: 3. Index at which (z0) coordinates are stored. 
    tree_id_field: int. default value: 4. Index at which cluster ID is stored. 

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------
    
    tree_heights: numpy array. Matrix containing (x, y, z) coordinates of each tree's
    highest point, as well as its normalized height and a binary field stating if the
    axis was deviated (1) or if it was not (0).
    '''
    
    
    
    # The cloud is re-voxelated to a larger resolution to then be clusterized.
    # Small clusters containing 1-2 voxels will be discarded to eliminate outliers points
    # that could interfere in height measurement.
    large_voxels_cloud, large_vox_to_cloud_ind, cloud_to_large_vox_ind = voxelate(voxelated_cloud, resolution_heights, resolution_heights, n_digits, X_field, Y_field, Z_field, with_n_points = False)

    # eps for DBSCAN
    eps_heights = resolution_heights * 1.9
    
    # Large-resolution voxelated cloud is clusterized
    clustering = DBSCAN(eps = eps_heights, min_samples = 2).fit(large_voxels_cloud) 
    
    # Cluster labels are attached to the fine-resolution voxelated cloud
    voxelated_cloud = np.append(voxelated_cloud, np.expand_dims(clustering.labels_[large_vox_to_cloud_ind], axis = 1), axis = 1)
    
    # Tree IDS are attached to the fine-resolution voxelated cloud too
    voxelated_cloud = np.append(voxelated_cloud, np.expand_dims(tree_id_vector, axis = 1), axis = 1)

    # Eliminating all points too far away from axes
    voxelated_cloud = voxelated_cloud[dist_to_axis < d, :]

    # Set of all cluster labels and their cardinality: cluster_id = {1,...,K}, K = 'number of clusters'.
    cluster_id, K = np.unique(clustering.labels_, return_counts = True)

    # Filtering of labels associated only to clusters that contain a minimum number of points.
    large_clusters = cluster_id[K > 3]

    # Discarding points that do not belong to any cluster
    large_clusters = large_clusters[large_clusters != -1]

    # Eliminating all points that belong to clusters with less than 2 points (large voxels)
    voxelated_cloud = voxelated_cloud[np.isin(voxelated_cloud[:, -2], large_clusters)]
    
    n_trees = detected_trees.shape[0]
    tree_heights = np.zeros((n_trees, 5))
    
    for i in range(n_trees): # Last row of tree_vector 
        
        # Be aware this finds the highest voxel (fine-resolution), not the highest point.
        valid_id = detected_trees[i, 0]
        single_tree = voxelated_cloud[voxelated_cloud[:, -1] == valid_id , 0:3] # Just the (x, y, z) coordinates
        which_z_max = np.argmax(single_tree[:, 2]) # The highest (z) value
        highest_point = single_tree[which_z_max, :] # The highest point
        tree_heights[i, 0:3] = highest_point
        tree_heights[i, 3] = highest_point[2] - detected_trees[i, 7] # (z0)
        
        # If tree is deviated from vertical, 1, else, 0.
        if (detected_trees[i, -1] > [max_dev]):
            
            tree_heights[i, -1] = 0
        else:
            tree_heights[i, -1] = 1
    
    return(tree_heights)



#-----------------------------------------------------------------------------------------------------------------------------------
# individualize_trees
#-----------------------------------------------------------------------------------------------------------------------------------

def individualize_trees(cloud, clust_stripe, resolution_z, resolution_xy, d_max, h_range, min_points, d, max_dev, filename_las, resolution_heights = 0.3, n_digits = 5, X_field = 0, Y_field = 1, Z_field = 2, Z0_field = 3, tree_id_field = 4):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    Function to be used AFTER the verticality clustering. It expects a filtered (based on the clustering process) 
    stripe as input, so that it only contains (hopefully) stems.
    Those stems are voxelated and enumerated, and then, their axes are identified using PCA 
    (PCA1 direction). This allows to group points based on their distance to those axes, 
    thus assigning each point to a tree. This last step is applied to the WHOLE original cloud.
    It also measures tree heights.

    It requires a Z0 field containing normalized heights in order to function properly.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    cloud: numpy array. the point cloud containing the forest plot. It is expected to have X, Y, Z and Z0 fields.
    clust_stripe: numpy array. The point cloud containing the clusterized stripe from verticality_clustering_iteration. 
    It is expected to have X, Y, Z and cluster ID fields.
    resolution_z: float. (x, y) voxel resolution.
    resolution_xy: float. (z) voxel resolution.
    d_max: float. Points that are closer than d_max to an axis are assigned to that axis.
    h_range: float. only stems where points extend vertically throughout a range as tall as defined by h_range are considered
    min_points: int. Minimum number of points in a cluster for it to be considered as a potential stem.
    d: float. Points within this distance from tree axis will be considered as potential points to define
    tree height.
    filename_las: char. File name for the output file.
    max_dev: float. Maximum degree of vertical deviation of a tree axis to consider its tree height measurement as valid.
    n_digits: int. default value: 5. Number of digits dedicated to each coordinate ((x), (y) or (z))
    during the generation of each point code. If the cloud is really large, it can be advisable
    to increase n_digits.
    X_field: int. default value: 0. Index at which (x) coordinate is stored.
    Y_field: int. default value: 1. Index at which (y) coordinate is stored.
    Z_field: int. default value: 2. Index at which (z) coordinate is stored.
    Z0_field: int. default value: 3. Index at which (z0) coordinate is stored. 
    tree_id_field: int. default value: 4. Index at which cluster ID is stored. 

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    assigned_cloud: numpy array. Point cloud containing individualized trees. 
    It consists of 6 columns: (x), (y), (z) and (z0) coordinates, a 5th column containing tree ID 
    that each point belongs to and a 6th column containing point distance to closest axis.
    detected_trees: numpy array. Matrix with as many rows as trees, containing a description of each 
    individualized tree. It stores the following values: tree ID, PCA1 X value, PCA1 Y value, PCA1 Z value,
    stem centroid X value, stem centroid Y value, stem centroid Z value, height difference of stem centroid (z - z0),
    axis vertical deviation.
    tree_heights: numpy array. Matrix containing the heights of individualized trees. It consists of 5 columns: 
    (x), (y), (z) and (z0) coordinates of the highest point of the tree and 5th column containing a
    binary indicator: 0 - tree was too deviated from vertical, and height may not be accurate;
    1 - tree was not too deviated from vertical, thus height may be trusted.
    '''

    # Whole original cloud voxelization
    voxelated_cloud, vox_to_cloud_ind, cloud_to_vox_ind = voxelate(cloud, resolution_z, resolution_xy, n_digits, X_field, Y_field, Z_field, with_n_points = False)
    
    # Call to compute_axes
    detected_trees, dist_to_axis, tree_id_vector = compute_axes(voxelated_cloud, clust_stripe, min_points, h_range, d_max, X_field, Y_field, Z_field, Z0_field, tree_id_field)   
    
    # Call to compute_heights
    tree_heights = compute_heights(voxelated_cloud, detected_trees, dist_to_axis, tree_id_vector, d, max_dev, resolution_heights, n_digits, X_field, Y_field, Z_field, Z0_field)
        
    las_tree_heights = laspy.create(point_format = 2, file_version='1.2')
    las_tree_heights.x = tree_heights[:, 0] # x
    las_tree_heights.y = tree_heights[:, 1] # y
    las_tree_heights.z = tree_heights[:, 2] # z
    las_tree_heights.add_extra_dim(laspy.ExtraBytesParams(name = "z0", type = np.int32))
    las_tree_heights.z0 = tree_heights[:, 3] # z0
    las_tree_heights.add_extra_dim(laspy.ExtraBytesParams(name = "deviated", type = np.int32))
    las_tree_heights.deviated = tree_heights[:, 4] # vertical deviation binary indicator
    las_tree_heights.write(filename_las[: -4] + "_tree_heights.las")
 

    # Two new fields are added to the original cloud: - tree ID (id of closest axis) - distance to that axis
    assigned_cloud = np.append(cloud, tree_id_vector[vox_to_cloud_ind, np.newaxis], axis = 1)
    assigned_cloud = np.append(assigned_cloud, dist_to_axis[vox_to_cloud_ind, np.newaxis], axis = 1)
    
    # Output: - Assigned cloud (X, Y, Z, Z0, tree_id, dist_to_axis) - tree vector 
    return assigned_cloud, detected_trees, tree_heights

#-----------------------------------------------------------------------------------------------------------------------------------
# point_clustering
#----------------------------------------------------------------------------------------------------------------------------------------                  

def point_clustering(X, Y, max_dist):      

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function clusters points by distance and finds the largest cluster.
    It will be used during circle fitting stage.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X: numpy array. Vector containing (x) coordinates of points belonging to a tree section. 
    Y: numpy array. Vector containing (y) coordinates of points belonging to a tree section. 
    max_dist: float. Max separation among the points to be considered as members of the same cluster.
    
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    X_g: numpy array. Vector containing the (x) coordinates of the largest cluster.
    Y_g: numpy array. Vector containing the (y) coordinates of the largest cluster.
    '''
    
    # Stacks 1D arrays ([X], [Y]) into a 2D array ([X, Y])
    xy_stack = np.column_stack((X, Y))
    
    # fclusterdata outputs a vector that contains cluster ID of each point (which cluster does each point belong to)
    clust_id = sch.fclusterdata(xy_stack, max_dist, criterion = 'distance', metric = 'euclidean')
    
    
    # Set of all clusters
    clust_id_unique = np.unique(clust_id)
    
    # For loop that iterates over each cluster ID, sums its elements and finds the largest
    n_max = 0
    for c in clust_id_unique: 
        
        # How many elements are in each cluster
        n = np.sum(clust_id == c)
        
        # Update largest cluster and its cardinality
        if n > n_max:
            n_max = n
            largest_cluster = c
            
    # X, Y coordinates of points that belong to the largest cluster
    X_g = xy_stack[clust_id == largest_cluster, 0] 
    Y_g = xy_stack[clust_id == largest_cluster, 1]
    
    # Output: those X, Y coordinates 
    return X_g, Y_g 
 


#-------------------------------------------------------------------------------------------------------------------------------------------------------
# fit_circle
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def fit_circle(X, Y):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function fits points within a tree section into a circumference by least squares minimization.
    Its intended inputs are X, Y coordinates of points belonging to a section.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X: numpy array. Vector containing (x) coordinates of points belonging to a tree section. 
    Y: numpy array. Vector containing (y) coordinates of points belonging to a tree section. 
    
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    circle_c: numpy array. Matrix containing the (x, y) coordinates of the circumference center.
    mean_radius: numpy array. Vector containing the radius of each fitted circumference.
    '''
    
    # Function that computes distance from each 2D point to a single point defined by (X_c, Y_c)
    # It will be used to compute the distance from each point to the circumference center.
    def calc_R(X, Y, X_c, Y_c):
        return np.sqrt((X - X_c) ** 2 + (Y - Y_c) ** 2)

    # Function that computes algebraic distance from each 2D point to some middle circle c
    # It calls calc_R (just defined above) and it is used during the least squares optimization.
    def f_2(c, X, Y):
        R_i = calc_R(X, Y, *c)
        return R_i - R_i.mean()

    # Initial barycenter coordinates (middle circle c center)
    X_m = X.mean()
    Y_m = Y.mean()
    barycenter = X_m, Y_m
  
  # Least square minimization to find the circumference that best fits all points within the section.
    circle_c, ier = opt.leastsq(f_2, barycenter, args = (X, Y)) # ier is a flag indicating whether the solution was found (ier = 1, 2, 3 or 4) or not (otherwise).
    X_c, Y_c = circle_c

  # Its radius 
    radius = calc_R(X, Y, *circle_c)
    mean_radius = radius.mean()
  
  # Output: - X, Y coordinates of best-fit circumference center - its radius
    return (circle_c, mean_radius)



#--------------------------------------------------------------------------------------------------------------------------------------------------------  
# inner_circle      
#--------------------------------------------------------------------------------------------------------------------------------------------------------

def inner_circle(X, Y, X_c, Y_c, R, times_R = 0.5):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    Function that computes an internal circumference inside the one fitted by fit_circle (the one that best fits all points within a section by least squares minimization).
    This new circumference is used as a validation tool: it gives insight on the quality of the 'fit_circle-circumference':
      - If points are closest to the inner circumference, then the first fit was not appropiate
      - On the contrary, if points are closer to the outer circumference, the 'fit_circle-circumference' is appropiate and describes well the stem diameter.
    Instead of directly computing the inner circle, it just takes a proportion (less than one) of the original circumference radius and its center.
    After this, it just checks how many points are closest to the inner circle than to the original circumference.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X: numpy array. Vector containing (x) coordinates of points belonging to a tree section. 
    Y: numpy array. Vector containing (y) coordinates of points belonging to a tree section. 
    X_c: numpy array. Vector containing (x) coordinates of fitted circumferences.
    Y_c: numpy array. Vector containing (y) coordinates of fitted circumferences.
    R: numpy array. Vector containing the radia of the fitted circumferences.
    
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    n_points_in: numpy array. Vector containing the number of points inside the inner circle of each section.
    '''
    
    # Distance from each 2D point to the center. 
    distance = np.sqrt((X - X_c) ** 2 + (Y - Y_c) ** 2) 
    
    # Number of points closest to the inner circumference, whose radius is proportionate to the outer circumference radius by a factor defined by 'times_R'.
    n_points_in = np.sum(distance < R * times_R) 
    
    # Output: Number of points closest to the inner circumference. 
    return n_points_in



#-------------------------------------------------------------------------------------------------------------------------------------------------------
# sector_occupancy
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def sector_occupancy(X, Y, X_c, Y_c, R, n_sectors = 16, min_n_sectors = 9, width = 2.0):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function provides quality measurements for the fitting of the circle.
    It divides the section in a number of sectors to check if there are points within them 
    (so they are occupied). It is divided in 16 sectors by default.
    If there are not enough occupied sectors, the section fails the test, as it is safe to asume it has an anomale, non desirable structure.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X: numpy array. Vector containing (x) coordinates of points belonging to a tree section. 
    Y: numpy array. Vector containing (y) coordinates of points belonging to a tree section. 
    X_c: numpy array. Vector containing (x) coordinates of fitted circumferences.
    Y_c: numpy array. Vector containing (y) coordinates of fitted circumferences.
    R: numpy array. Vector containing the radia of the fitted circumferences.
    n_sectors: int. default value: 16. Number of sectors in which the sections will be divided 
    min_n_sectors: int. default value: 9. Minimum number of occupied sectors in a section for its fitted circumference to be considered as valid.
    width: float. default value: 2.0. Width (cm) around the fitted circumference to look for points.
    
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    perct_occuped_sectors: numpy array. Vector containing the percentage of occupied sectors in each section.
    enough_occuped_sectors: numpy array. Vector containing binary indicators whether the fitted circle is valid or not:
    1 - valid; 0 - not valid.
    '''
    
    # Coordinates translation.
    X_red = X - X_c
    Y_red = Y - Y_c
    
    # Computation of radius and angle necessary to transform cartesian coordinates to polar coordinates. 
    radial_coord  = np.sqrt(X_red ** 2 + Y_red ** 2) # radial coordinate
    angular_coord = np.arctan2(X_red, Y_red) # angular coordinate. This function from numpy directly computes it. 
    
    # Points that are close enough to the circumference that will be checked.
    points_within = (radial_coord > (R - width / 100)) * (radial_coord < (R + width / 100))
    
    # Codification of points in each sector. Basically the range of angular coordinates is divided in n_sector pieces and granted an integer number.
    # Then, every point is assigned the integer corresponding to the sector it belongs to.
    norm_angles = np.floor(angular_coord[points_within] / (2 * np.pi / n_sectors)) # np.floor se queda solo con la parte entera de la división
    
    # Number of points in each sector. 
    n_occuped_sectors = np.size(np.unique(norm_angles)) 
    
    # Percentage of occupied sectors.
    perct_occuped_sectors = n_occuped_sectors * 100 / n_sectors
    
    # If there are enough occupied sectors, then it is a valid section.
    if n_occuped_sectors < min_n_sectors:
        enough_occuped_sectors = 0
    
    # If there are not, then it is not a valid section.
    else:
        enough_occuped_sectors = 1
    
    # Output: percentage of occuped sectors | boolean indicating if it has enough occuped sectors to pass the test.
    return (perct_occuped_sectors, enough_occuped_sectors)# 0: no pasa; 1: pasa el test



#-------------------------------------------------------------------------------------------------------------------------------------
# fit_circle_check
#----------------------------------------------------------------------------------------------------------------------------------------

def fit_circle_check(X, Y, review, second_time, times_R, threshold, R_min, R_max, max_dist, n_points_section, n_sectors = 16, min_n_sectors = 9, width = 2):
     
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function calls fit_circle() to fit points within a section to a circumference by least squares
    minimization. These circumferences will define tree sections. It checks the goodness of fit 
    using the functions defined above. If fit is not appropriate, another circumference 
    will be fitted using only points from the largest cluster inside the first circumference. 
    
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X: numpy array. Vector containing (x) coordinates of points belonging to a tree section. 
    Y: numpy array. Vector containing (y) coordinates of points belonging to a tree section. 
    second_time: numpy array. Vector containing integers that indicates whether it is the first
    time a circle is fitted or not (will be modified internally).
    times_R: float. Ratio of radius between outer circumference and inner circumference.
    threshold: float. Minimum number of points in inner circumference for a fitted circumference to be valid.
    R_min: float. Minimum radius that a fitted circumference must have to be valid.
    R_max: float. Maximum radius that a fitted circumference must have to be valid.
    max_dist: float. Refer to point_clustering.
    n_points_section: int. Minimum points within a section for its fitted circumference to be valid.
    n_sectors: int. default value: 16. Number of sectors in which the sections will be divided 
    min_n_sectors: int. default value: 9. Minimum number of occupied sectors in a section for its fitted circumference to be considered as valid.
    width: float. default value: 2.0. Width (cm) around the fitted circumference to look for points.
    
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    X_gs: numpy array. Matrix containing (x) coordinates of largest clusters.
    Y_gs: numpy array. Matrix containing (y) coordinates of largest clusters.
    X_c: numpy array. Matrix containing (x) coordinates of the center of the best-fit circumferences.
    Y_c: numpy array. Matrix containing (y) coordinates of the center of the best-fit circumferences.
    R: numpy array. Vector containing best-fit circumference radia.
    section_perct: numpy array. Matrix containing the percentage of occupied sectors.
    n_points_in: numpy array. Matrix containing the number of points in the inner circumferences.
    '''
    
    # If loop that discards sections that do not have enough points (n_points_section)
    if X.size > n_points_section:
      
        # Call to fit_circle to fit the circumference that best fits all points within the section. 
        (circle_center, R) = fit_circle(X = X, Y = Y)
        X_c = circle_center[0] # Column 0 is center X coordinate 
        Y_c = circle_center[1] # Column 1 is center Y coordinate 
        
        # Call to inner_circle to fit an inner circumference and to get the number of points closest to it. 
        n_points_in = inner_circle(X, Y, X_c, Y_c, R, times_R)

        # Call to sector_occupancy to check if sectors around inner circumference are occupied.
        (sector_perct, enough_sectors) = sector_occupancy(X, Y, X_c, Y_c, R, n_sectors, min_n_sectors, width)
        
        # If any of the following conditions hold:
        #   - Too many points in inner circle
        #   - Radius of best-fit circle is too small
        #   - Number of occupied sectors is too low
        # Then proceed with countermeasures
        if n_points_in > threshold or R < R_min or R > R_max or enough_sectors == 0:
            
            # If this is not the second round or, simply, if it is the first round, then proceed
            if second_time == 0:
                 
                 # First round implies there is no X_g or Y_g, as points would not have been grouped yet. point_clustering is called.
                (X_g, Y_g) = point_clustering(X, Y, max_dist) #X_g or Y_g are the coordinates of the largest cluster.
                
                # If cluster size is big enough, then proceed. It is done this way to account for cases where, even though the section had enough points,
                # there might not be enough points within the largest cluster.
                if X_g.size > n_points_section: 
    
                     # Call to fit_circle_check (lets call it the 'deep call'). Now it is guaranteed that it is a valid section (has enough points and largest cluster has enough points as well).
                    (X_c, Y_c, R, review, second_time, sector_perct, n_points_in) = fit_circle_check(X_g, Y_g, 0, 1, times_R, threshold, R_min, R_max, max_dist, n_points_section, n_sectors, min_n_sectors, width)
                    
                # If cluster size is not big enough, then don't take the section it belongs to into account. 
                else:
                    review = 1 # Even if it is not a valid section, lets note it has been checked.
                    X_c = 0
                    Y_c = 0
                    R = 0
                    second_time = 1
            
            # If this is the second round (whether the first round succesfully provided a valid section or not), then proceed.        
            else:
                review = 1 # Just stating that if this is the second round, the check has, obviously, happened.
    
    # This matches the first loop. If section is not even big enough (does not contain enough points), it is not valid.
    else:
        review = 2
        X_c = 0
        Y_c = 0
        R = 0
        second_time = 2
        sector_perct = 0
        n_points_in = 0
    
    # Output is basically the one obtained during the 'deep call', if the section was valid.
    # If not, it is basically empty values (actually zeros).
    # X_gs, Y_gs are actually never used again, they are kept just in case they would become useful in a future update.
    # X_c, Y_c are the coordinates of the center of the best-fit circumference an R its radius.
    # section_perct is the percentage of occupied sectors, and n_points_in is the number of points closest to the inner circumference (quality measurements).
    return X_c, Y_c, R, review, second_time, sector_perct, n_points_in
    


#-------------------------------------------------------------------------------------------------------------------------------------------------------
# tilt_detection
#-------------------------------------------------------------------------------------------------------------------------------------------------------

# relat_peso_outliers_suma_inclinaciones = w_1
# relat_peso_outliers_relativos = w_2


def tilt_detection(X_tree, Y_tree, radius, Z_section, Z_field = 2, w_1 = 3.0, w_2 = 1.0):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function finds outlier tilting values among sections within a tree and assigns a score to the sections based on those outliers.
    There are two kinds of outliers: absolute and relative outliers.
    Absolute outliers are obtained from the sum of the deviations from every section center to all axes within a tree (the most tilted sections relative to all axes)
    Relative outliers are obtained from the deviations of other section centers from a certain axis, within a tree (the most tilted sections relative to a certain axis)
    The 'outlier score' consists on a weighted sum of the absolute tilting value and the relative tilting value.
    
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X_tree: numpy array. Matrix containing (x) coordinates of the center of the sections.
    Y_tree: numpy array. Matrix containing (y) coordinates of the center of the sections. 
    radius: numpy array. Vector containing section radia.
    Z_section: numpy array. Vector containing the height of the section associated to each section.
    Z_field: int. default value: 2. Index at which (z) coordinate is stored.
    w_1: float. default value: 3.0. Weight of absolute deviation.
    w_2: float. default value: 1.0. Weight of relative deviation.
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    outlier_prob: numpy array. Vector containing the 'outlier probability' of each section.
    '''
    
    # This function simply defines 1st and 3rd cuartile of a vector and separates values that are outside the interquartilic range
    # defined by these. Those are the candidates to be outliers. This filtering may be done either directly from the interquartilic range,  
    # or from a certain distance from it, thanks to 'n_range' parameter. Its default value is 1.5.
    
    def outlier_vector(vector, lower_q = 0.25, upper_q = 0.75, n_range = 1.5):
        
        q1 = np.quantile(vector, lower_q) # First quartile
        q3 = np.quantile(vector, upper_q) # Third quartile
        iqr = q3 - q1 # Interquartilic range

        lower_bound = q1 - iqr * n_range # Lower bound of filter. If n_range = 0 -> lower_bound = q1
        upper_bound = q3 + iqr * n_range # Upper bound of filter. If n_range = 0 -> upper_bound = q3
        
        # Outlier vector.
        outlier_ind = (vector < lower_bound) | (vector > upper_bound) * 1 # ? why would you multiply times 1?
        return outlier_ind

    # Empty matrix that will store the probabilities of a section to be invalid
    outlier_prob = np.zeros_like(X_tree)
    
    # First loop: iterates over each tree
    for i in range(X_tree.shape[0]):
        
        # If there is, at least, 1 circle with positive radius in a tree, then proceed (invalid circles are stored with a radius value of 0)
        if np.sum(radius[i, :]) > 0:
            
            # Filtering sections within a tree that have valid circles (non-zero radius).
            valid_radius = radius[i, :] > 0
            
            # Weights associated to each section. They are computed in a way that the final value of outliers sums up to 1 as maximum.  
            abs_outlier_w = w_1 / (np.size(Z_section[valid_radius]) * w_2 + w_1)
            rel_outlier_w = w_2 / (np.size(Z_section[valid_radius]) * w_2 + w_1)
    
             
            # Vertical distance matrix among all sections (among their centers)
            heights = np.zeros((np.size(Z_section[valid_radius]), Z_field)) # Empty matrix to store heights of each section
            heights[:, 0] = np.transpose(Z_section[valid_radius]) #  Height (Z value) of each section
            z_dist_matrix = distance_matrix(heights, heights) # Vertical distance matrix
    
            # Horizontal distance matrix among all sections (among their centers)
            c_coord = np.zeros((np.size(Z_section[valid_radius]), 2))  # Empty matrix to store X, Y coordinates of each section
            c_coord[:, 0] = np.transpose(X_tree[i][valid_radius]) # X coordinates
            c_coord[:, 1] = np.transpose(Y_tree[i][valid_radius]) # Y coordinates
            xy_dist_matrix = distance_matrix(c_coord, c_coord) # Horizontal distance matrix
            
            # Tilting measured from every vertical within a tree: All verticals obtained from the set of sections within a tree.
            # For instance, if there are 10 sections, there are 10 tilting values for each section.
            tilt_matrix = np.arctan(xy_dist_matrix / z_dist_matrix) * 180 / np.pi
            
            # Summation of tilting values from each center.
            tilt_sum = np.nansum(tilt_matrix, axis = 0)
            
            # Outliers within previous vector (too low / too high tilting values). These are anomalus tilting values from ANY axis. 
            outlier_prob[i][valid_radius] = outlier_vector(tilt_sum) * abs_outlier_w
            
            # Second loop: iterates over each section (within a single tree).
            for j in range(np.size(Z_section[valid_radius])):
                
                # Search for anomalous tilting values from a CERTAIN axis. 
                tilt_matrix[j, j] = np.quantile(tilt_matrix[j, ~j], 0.5)
                rel_outlier = outlier_vector(tilt_matrix[j]) * rel_outlier_w # Storing those values.
                
                # Sum of absolute outlier value and relative outlier value
                outlier_prob[i][valid_radius] = outlier_prob[i][valid_radius] + rel_outlier
            
            # Freeing memory    
            del c_coord, xy_dist_matrix, tilt_matrix, tilt_sum, rel_outlier, j
    
    # Freeing memory        
    del i, z_dist_matrix
    
    # Output: Oulier value: Value associated to each outlier associated to their tilting.
    return outlier_prob



#-------------------------------------------------------------------------------------------------------------------------------------------------------
# draw_circles
#-------------------------------------------------------------------------------------------------------------------------------------------------------


def draw_circles(X_c, Y_c, R, sections, check_circle, sector_perct, n_points_in, tree_vector, outliers, R_min, R_max, threshold, n_sectors, min_n_sectors, filename_las, circa_points = 200):
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function generates points that comprise the circles computed by fit_circle function, 
    so sections can be visualized.
    The circles are then saved in a LAS file, along some descriptive fields.
    Each circle corresponds on a one-to-one basis to the sections described by the user (they are input by 'sections' parameter).

    
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    X_c: numpy array. Matrix containing (x) coordinates of the center of the sections.
    Y_c: numpy array. Matrix containing (y) coordinates of the center of the sections. 
    R: numpy array. Vector containing section radia.
    sections: numpy array. Vector containing section heights (normalized heights).
    section_perct: numpy array. Matrix containing the percentage of occupied sectors.
    n_points_in: numpy array. Matrix containing the number of points in the inner circumferences.
    tree_vector: numpy array. detected_trees output from individualize_trees.
    outliers: numpy array. Vector containing the 'outlier probability' of each section.
    filename_las: char. File name for the output file.
    circa_points: int. Number of points to draw each circle.

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    Output is a LAS file containing the circles.
    '''
    
    # Empty vector to be filled. It has as many elements as the vector containing the center of the circles for a given tree.
    tree_section = X_c.shape
    
    # Empty array that will contain the information about each section, to then be used to complete the .LAS file data.
    section_c_xyz = np.zeros([tree_section[0] * tree_section[1], 9])
    
    # Auxiliar index indicating which section is in use.
    section = 0
    
    # Double for loop to iterate through each combination of coordinates
    for i in range(tree_section[0]):
        for j in range(tree_section[1]):
            
            # If distance is within range (0, 1), then proceed.
            if R[i, j] > 0 and R[i, j] < 1:
              
                # Filling the array with the appropiate data
                section_c_xyz[section, :] = [X_c[i, j], Y_c[i, j], sections[j] + tree_vector[i, 7], R[i, j], check_circle[i, j], sector_perct[i,j], n_points_in[i, j], sections[j], outliers[i, j]]
                
                section = section + 1
    
    
    # Just the centers of each filled section
    centers = section_c_xyz[:section, :]
    
    # Number of centers
    n = centers.shape[0]
    
    # Empty vector to be filled with the coordinates of each circle.
    coords = np.zeros((circa_points * n, 11))
    
    # User-create function to tranform polar coordinates to cartesian coordinates.
    def polar_to_cart(theta, rho):
        x = rho * np.cos(theta)
        y = rho * np.sin(theta)
        return x, y
    
    # For loop to iterate over each circle and compute their (x, y) coordinates. (z) coordinates are already given by the user.
    for i in range(n):
        start = i * circa_points
        end = (i + 1) * circa_points
        angles = np.arange(0, 2 * np.pi, 2 * np.pi / circa_points)
        radius = centers[i, 3]
        (x, y) = polar_to_cart(angles, radius)
        
        coords[start:end, 0] = x + centers[i, 0]# X
        coords[start:end, 1] = y + centers[i, 1]# Y
        coords[start:end, 2] = centers[i, 2]# check
        coords[start:end, 3] = centers[i, 4]# Z0
        coords[start:end, 4] = i # Tree ID
        coords[start:end, 5] = centers[i, 5]# sector occupancy
        coords[start:end, 6] = centers[i, 6]# points in inner circle
        coords[start:end, 7] = centers[i, 7]# Z0
        coords[start:end, 8] = centers[i, 3] * 2 # Diameter
        coords[start:end, 9] = centers[i, 8]# outlier probability 
               
        if (centers[i, 5] < min_n_sectors / n_sectors * 100) | (centers[i, 6] > threshold) | (centers[i, 8] > 0.3) | (centers[i, 3] < R_min) | (centers[i, 3] > R_max): # only happens when which_dbh == 0 # which_valid_points should be used here
            coords[start:end, 10] = 1 # does not pass quality checks
        else:
            coords[start:end, 10] = 0 # passes quality checks

    # LAS file containing circle coordinates. 
    las_circ = laspy.create(point_format = 2, file_version='1.2')
    las_circ.x = coords[:, 0]
    las_circ.y = coords[:, 1]
    las_circ.z = coords[:, 2]
    
    # All extra fields.
    
    # las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "check", type = np.int32))
    # las_circ.check = coords[:, 3]
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "tree_ID", type = np.int32))
    las_circ.tree_ID = coords[:, 4]
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "sector_occupancy_percent", type = np.float64))
    las_circ.sector_occupancy_percent = coords[:, 5]
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "pts_inner_circle", type = np.int32))
    las_circ.pts_inner_circle = coords[:, 6]
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "Z0", type = np.float64))
    las_circ.Z0 = coords[:, 7]
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "Diameter", type = np.float64))
    las_circ.Diameter = coords[:, 8]   
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "outlier_prob", type = np.float64))
    las_circ.outlier_prob = coords[:, 9] 
    
    las_circ.add_extra_dim(laspy.ExtraBytesParams(name = "quality", type = np.int32))
    las_circ.quality = coords[:, 10]
    
    las_circ.write(filename_las[: -4] + "_circ.las")

    return(coords)


#-------------------------------------------------------------------------------------------------------------------------------------------------------
# draw_axes
#-------------------------------------------------------------------------------------------------------------------------------------------------------

# Function that draws the axes computed for each tree.

def draw_axes(tree_vector, line_downstep, line_upstep, stripe_lower_limit, stripe_upper_limit, point_interval, filename_las, X_field = 0, Y_field = 1, Z_field = 2):
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function generates points that comprise the axes computed by individualize_trees, 
    so they can be visualized.
    The axes are then saved in a LAS file, along some descriptive fields.
    Each circle corresponds on a one-to-one basis to the individualized trees.
    
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    tree_vector: numpy array. detected_trees output from individualize_trees.
    line_downstep: float. It will be used to derive the position from which steps will start to locate points downstep the stem centroids.
    line_upstep: float. It will be used to derive the position from which steps will start to locate points upstep the stem centroids.
    stripe_lower_limit: float. Lower point of the axis drawn. 
    stripe_upper_limit: float. Upper point of the axis drawn. 
    point_interval: float. Step value used to draw points.
    filename_las: char. File name for the output file.
    X_field: int. default value: 0. Index at which (x) coordinate is stored.
    Y_field: int. default value: 1. Index at which (y) coordinate is stored.
    Z_field: int. default value: 2. Index at which (z) coordinate is stored.


    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    Output is a LAS file containing the axes.
    '''
    
    stripe_centroid = (stripe_lower_limit + stripe_upper_limit) / 2
    mean_descend = stripe_centroid + line_downstep 
    mean_rise = line_upstep - stripe_centroid 
 
    up_iter = np.round(mean_rise / point_interval)
    down_iter = mean_descend / point_interval

    axes_points = np.zeros((np.int_(tree_vector.shape[0] * (up_iter + down_iter)), 3))
    tilt = np.zeros(np.int_(tree_vector.shape[0] * (up_iter + down_iter)))
    ind = 0 
    
    for i in range(tree_vector.shape[0]): 
        
        if np.sum(np.exp2(tree_vector[i, 1:4])) > 0:
            
            if tree_vector[i, 3] < 0: 
                
                vector = -tree_vector[i, 1:4]
                
            else:
              
                vector = tree_vector[i, 1:4]
                
            axes_points[np.int_(ind):np.int_(ind + up_iter + down_iter), :] = np.transpose([np.arange(-down_iter, up_iter), np.arange(-down_iter, up_iter), np.arange(-down_iter, up_iter)]) * vector * point_interval + tree_vector[i,4:7]
            tilt[np.int_(ind):np.int_(ind + up_iter + down_iter)] = tree_vector[i, 8]
            ind = ind + up_iter + down_iter
            
    axes_points = axes_points[:np.int_(ind), :]
    las_axes = laspy.create(point_format = 2, file_version = '1.2')
    las_axes.x = axes_points[:, X_field]
    las_axes.y = axes_points[:, Y_field]
    las_axes.z = axes_points[:, Z_field]
    las_axes.add_extra_dim(laspy.ExtraBytesParams(name = "tilting_degree", type = np.float64))
    las_axes.tilting_degree = tilt
    
    las_axes.write(filename_las[:-4] + "_axes.las")


#-------------------------------------------------------------------------------------------------------------------------------------------------------
# tree_locator
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def tree_locator(sections, X_c, Y_c, tree_vector, sector_perct, R, n_points_in, threshold, outliers, filename_las, X_field = 0, Y_field = 1, Z_field = 2):

    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function generates points that locate the individualized trees and computes
    their DBH (diameter at breast height). It uses all the quality measurements defined in previous
    functions to check whether the DBH should be computed or not and to check which point should
    be used as the tree locator.
    
    The tree locators are then saved in a LAS file. Each tree locator corresponds on a one-to-one basis to the individualized trees.
    
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    sections: numpy array. Vector containing section heights (normalized heights).
    X_c: numpy array. Matrix containing (x) coordinates of the center of the sections.
    Y_c: numpy array. Matrix containing (y) coordinates of the center of the sections. 
    tree_vector: numpy array. detected_trees output from individualize_trees.
    sector_perct: numpy array. Matrix containing the percentage of occupied sectors.
    R: numpy array. Vector containing section radia.
    n_points_in: numpy array. Matrix containing the number of points in the inner circumferences.
    threshold: float. Minimum number of points in inner circumference for a fitted circumference to be valid.
    outliers: numpy array. Vector containing the 'outlier probability' of each section.
    filename_las: char. File name for the output file.
    X_field: int. default value: 0. Index at which (x) coordinate is stored.
    Y_field: int. default value: 1. Index at which (y) coordinate is stored.
    Z_field: int. default value: 2. Index at which (z) coordinate is stored.


    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    Output is a LAS file containing the axes and two objects:
    dbh_values: numpy array. Vector containing DBH values.
    tree_locations: numpy array. matrix containing (x, y, z) coordinates of each tree_locator.
    '''
    
    dbh = 1.3 # Breast height
    
    tree_locations = np.zeros(shape = (X_c.shape[0], 3)) #Empty vector to be filled with tree locators
    n_trees = tree_locations.shape[0] # Number of trees
    
    dbh_values = np.zeros(shape = (X_c.shape[0], 1)) # Empty vector to be filled with DBH values.
    
    # This if loop covers the cases where the stripe was defined in a way that it did not include BH
    # and DBH nor tree locator cannot be obtained from a section at or close to BH. If that happens, tree axis is used
    # to locate the tree and DBH is not computed.
    if np.min(sections) > 1.3:
        
      for i in range(n_trees): 
          
          if tree_vector[i, 3] < 0:
              
              vector = -tree_vector[i, 1:4]
          
          else:
              
              vector = tree_vector[i, 1:4]
          
          diff_height = dbh - tree_vector[i, 6] + tree_vector[i, 7]  # Compute the height difference between centroid and BH
          dist_centroid_dbh = diff_height / np.cos(tree_vector[i, 8] * np.pi / 180)  # Compute the distance between centroid and axis point at BH.      
          tree_locations[i, :] = vector * dist_centroid_dbh + tree_vector[i, 4:7] # Compute coordinates of axis point at BH. 

    else:
          
        d = 1
        diff_to_dbh = sections - dbh # Height difference between each section and BH.
        which_dbh = np.argmin(np.abs(diff_to_dbh)) # Which section is closer to BH.
      
        # get surrounding sections too
        lower_d_section = which_dbh - d
        upper_d_section = which_dbh + d
        
        # Just in case they are out of bound
        if lower_d_section < 0:
            
            lower_d_section = 0
        
        if upper_d_section > sections.shape[0]:
            
            upper_d_section = sections.shape[0]
            
        # BH section and its neighbours. From now on, neighbourhood
        close_to_dbh = np.array(np.arange(lower_d_section, upper_d_section)) 
     
        for i in range(n_trees): # For each tree
        
            which_valid_R = R[i, close_to_dbh] > 0 # From neighbourhood, select only those with non 0 radius
            which_valid_out = outliers[i, close_to_dbh] < 0.30 #From neighbourhood, select only those with outlier probability lower than 10 %
            which_valid_sector_perct = sector_perct[i, close_to_dbh] > 30 # only those with sector occupancy higher than 30 %
            which_valid_points = n_points_in[i, close_to_dbh] > threshold # only those with enough points in inner circle
            
            # If there are valid sections among the selected
            if (np.any(which_valid_R)) & (np.any(which_valid_out)):
                
                # If first section is BH section and if itself and its only neighbour are valid
                if (lower_d_section == 0) & (np.all(which_valid_R)) & (np.all(which_valid_out)) & np.all(which_valid_sector_perct): # only happens when which_dbh == 0 # which_valid_points should be used here
                
                    # If they are coherent: difference among their radia is not larger than 10 % of the largest radius
                    if np.abs(R[i, close_to_dbh[0]] - R[i, close_to_dbh[1]]) < np.max(R[i, close_to_dbh]) * 0.1:
                
                        dbh_values[i] = R[i, which_dbh] * 2
        
                        tree_locations[i, X_field] = X_c[i, which_dbh].flatten() # Their centers are averaged and we keep that value
                        tree_locations[i, Y_field] = Y_c[i, which_dbh].flatten() # Their centers are averaged and we keep that value
                        tree_locations[i, Z_field] = tree_vector[i, 7] + dbh # original height is obtained
                    
                    # If not all of them are valid, then there is no coherence in any case, and the axis location is used
                    else:
                        
                        if tree_vector[i, 3] < 0:
                        
                            vector = -tree_vector[i, 1:4]
                    
                        else:
                        
                            vector = tree_vector[i, 1:4]
                    
                        diff_height = dbh - tree_vector[i, 6] + tree_vector[i, 7]  # Compute the height difference between centroid and BH
                        dist_centroid_dbh = diff_height / np.cos(tree_vector[i, 8] * np.pi / 180)  # Compute the distance between centroid and axis point at BH.      
                        tree_locations[i, :] = vector * dist_centroid_dbh + tree_vector[i, 4:7] # Compute coordinates of axis point at BH. 

                # If last section is BH section and if itself and its only neighbour are valid    
                elif (upper_d_section == sections.shape[0]) & (np.all(which_valid_R)) & (np.all(which_valid_out)):
                
                        # if they are coherent
                        if np.abs(R[i, close_to_dbh[0]] - R[i, close_to_dbh[1]]) < np.max(R[i, close_to_dbh]) * 0.15:
                    
                            # use BH section diameter as DBH
                            dbh_values[i] = R[i, which_dbh] * 2
            
                            tree_locations[i, X_field] = X_c[i, which_dbh].flatten() # use its center x value as x coordinate of tree locator
                            tree_locations[i, Y_field] = Y_c[i, which_dbh].flatten() # use its center y value as y coordinate of tree locator
                            tree_locations[i, Z_field] = tree_vector[i, 7] + dbh
                        
                        # If not all of them are valid, then there is no coherence in any case, and the axis location is used and DBH is not computed
                        else:
                            
                            if tree_vector[i, 3] < 0:
                            
                                vector = -tree_vector[i, 1:4]
                        
                            else:
                            
                                vector = tree_vector[i, 1:4]
                        
                            dbh_values[i] = 0
                            
                            diff_height = dbh - tree_vector[i, 6] + tree_vector[i, 7]  # Compute the height difference between centroid and BH
                            dist_centroid_dbh = diff_height / np.cos(tree_vector[i, 8] * np.pi / 180)  # Compute the distance between centroid and axis point at BH.      
                            tree_locations[i, :] = vector * dist_centroid_dbh + tree_vector[i, 4:7] # Compute coordinates of axis point at BH. 

                # In any other case, BH section is not first or last section, so it has 2 neighbourghs
                # 3 posibilities left: 
                # A: Not all of three sections are valid: there is no possible coherence
                # B: All of three sections are valid, and there is coherence among the three
                # C: All of three sections are valid, but there is only coherence among neighbours and not BH section or All of three sections are valid, but there is no coherence
                else:
                
                    # Case A:
                    if not ((np.all(which_valid_R)) & (np.all(which_valid_out)) & np.all(which_valid_sector_perct)):
                        
                        if tree_vector[i, 3] < 0:
                        
                            vector = -tree_vector[i, 1:4]
                    
                        else:
                        
                            vector = tree_vector[i, 1:4]
                    
                        dbh_values[i] = 0
                        
                        diff_height = dbh - tree_vector[i, 6] + tree_vector[i, 7]  # Compute the height difference between centroid and BH
                        dist_centroid_dbh = diff_height / np.cos(tree_vector[i, 8] * np.pi / 180)  # Compute the distance between centroid and axis point at BH.      
                        tree_locations[i, :] = vector * dist_centroid_dbh + tree_vector[i, 4:7] # Compute coordinates of axis point at BH. 

                
                    else:
                        
                        valid_sections = close_to_dbh # Valid sections indexes
                        valid_radia = R[i, valid_sections] # Valid sections radia
                        median_radius = np.median(valid_radia) # Valid sections median radius
                        abs_dev = np.abs(valid_radia - median_radius) # Valid sections absolute deviation from median radius
                        mad = np.median(abs_dev) # Median absolute deviation
                        filtered_sections = valid_sections[abs_dev < 3 * mad] # Only keep sections close to median radius (3 MAD criterion)
                        
                        # 3 things can happen here:
                        # There are no deviated sections --> there is coherence among 3 --> case B
                        # There are 2 deviated sections --> only median radius survives filter --> case C

                        # Case B
                        if filtered_sections.shape[0] == close_to_dbh.shape[0]:
                            
                           dbh_values[i] = R[i, which_dbh] * 2
           
                           tree_locations[i, X_field] = X_c[i, which_dbh].flatten() # Their centers are averaged and we keep that value
                           tree_locations[i, Y_field] = Y_c[i, which_dbh].flatten() # Their centers are averaged and we keep that value
                           tree_locations[i, Z_field] = tree_vector[i, 7] + dbh
                        
                        # Case C
                        else:
                            # if PCA1 Z value is negative
                            if tree_vector[i, 3] < 0:
                            
                                vector = -tree_vector[i, 1:4]
                        
                            else:
                            
                                vector = tree_vector[i, 1:4]
                        
                            dbh_values[i] = 0
                            
                            diff_height = dbh - tree_vector[i, 6] + tree_vector[i, 7]  # Compute the height difference between centroid and BH
                            dist_centroid_dbh = diff_height / np.cos(tree_vector[i, 8] * np.pi / 180)  # Compute the distance between centroid and axis point at BH.      
                            tree_locations[i, :] = vector * dist_centroid_dbh + tree_vector[i, 4:7] # Compute coordinates of axis point at BH. 

               

            # If there is not a single section that either has non 0 radius nor low outlier probability, there is nothing else to do -> axis location is used 
            else: 
            
                if tree_vector[i, 3] < 0:
                
                    vector = -tree_vector[i, 1:4]
            
                else:
                
                    vector = tree_vector[i, 1:4]
            
                diff_height = dbh - tree_vector[i, 6] + tree_vector[i, 7]  # Compute the height difference between centroid and BH
                dist_centroid_dbh = diff_height / np.cos(tree_vector[i, 8] * np.pi / 180)  # Compute the distance between centroid and axis point at BH.      
                tree_locations[i, :] = vector * dist_centroid_dbh + tree_vector[i, 4:7] # Compute coordinates of axis point at BH. 

                dbh_values[i] = 0
                            
      
    
    las_tree_locations = laspy.create(point_format = 2, file_version = '1.2')
    las_tree_locations.x = tree_locations[:, X_field]
    las_tree_locations.y = tree_locations[:, Y_field]
    las_tree_locations.z = tree_locations[:, Z_field]


    las_tree_locations.write(filename_las[:-4] + "_tree_locator.las")
    
    return(dbh_values, tree_locations)

#-------------------------------------------------------------------------------------------------------------------------------------------------------
# clean_ground
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def clean_ground(cloud):
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function takes a point cloud and denoises it via DBSCAN clustering. It first 
    voxelates the point cloud into 0.15 m voxels, then clusters the voxel cloud and excludes
    clusters of size less than 2.

    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    cloud: numpy array. Matrix containing (x, y, z) coordinates of the points.

    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    clust_cloud: numpy array. Matrix containing (x, y, z) coordinates of the denoised points.
    '''
    
    vox_cloud, vox_to_cloud_ind, cloud_to_vox_ind = voxelate(cloud, 0.15, 0.15, with_n_points = False)
    # Cluster labels are appended to the FILTERED cloud. They map each point to the cluster they belong to, according to the clustering algorithm.
    clustering = DBSCAN(eps = 0.3, min_samples = 2).fit(vox_cloud)
    
    cloud_labs = np.append(cloud, np.expand_dims(clustering.labels_[vox_to_cloud_ind], axis = 1), axis = 1)
    
    # Set of all cluster labels and their cardinality: cluster_id = {1,...,K}, K = 'number of points'.
    cluster_id, K = np.unique(clustering.labels_, return_counts = True)
    
    # Filtering of labels associated only to clusters that contain a minimum number of points.
    large_clusters = cluster_id[K > 2]
    
    # ID = -1 is always created by DBSCAN() to include points that were not included in any cluster.
    large_clusters = large_clusters[large_clusters != -1]
    
    # Removing the points that are not in valid clusters.       
    clust_cloud = cloud_labs[np.isin(cloud_labs[:, -1], large_clusters), :3]
    return(clust_cloud)

#-------------------------------------------------------------------------------------------------------------------------------------------------------
# classify_ground
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def generate_dtm(cloud, bSloopSmooth = True, cloth_resolution = 0.5, classify_threshold = 0.1, exportCloth = True): 
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function takes a point cloud and generates a Digital Terrain Model (DTM) based on its ground.
    It's based on 'Cloth Simulation Filter' by: W. Zhang et al., 2016 (http://www.mdpi.com/2072-4292/8/6/501/htm),
    which is implemented on CSF package. This function just implements it in a convenient way for this use-case. 
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    cloud: numpy array. Matrix containing (x, y, z) coordinates of the points.
    bSloopSmooth: Boolean. default value: True. The resulting DTM will be smoothed. Refer to CSF documentation.
    cloth_resolution: float. default value: 0.5. The resolution of the cloth grid. Refer to CSF documentation.
    classify_threshold: float. default value: 0.1. The threshold used to classify the point cloud into ground and non-ground parts. Refer to CSF documentation.
    exportCloth: Boolean. default value = True. The DTM will be exported. Refer to CSF documentation.
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    cloth_nodes: numpy array. Matrix containing (x, y, z) coordinates of the DTM points.
    '''
    
    ### Cloth simulation filter ###
    csf = CSF.CSF() # initialize the csf

    ### parameter settings ###
    csf.params.bSloopSmooth = bSloopSmooth 
    csf.params.cloth_resolution = cloth_resolution
    # csf.params.rigidness # 1, 2 or 3
    csf.params.classify_threshold = classify_threshold # default is 0.5 m

    csf.setPointCloud(cloud) # pass the (x), (y), (z) list to csf
    ground = CSF.VecInt()  # a list to indicate the index of ground points after calculation
    non_ground = CSF.VecInt() # a list to indicate the index of non-ground points after calculation

    csf.do_filtering(ground, non_ground, exportCloth = exportCloth) # do actual filtering.
    
    # Retrieving the cloth nodes 
    with open('cloth_nodes.txt', 'r+') as f:
        l = [[float(num) for num in line.split('\t')] for line in f]

    cloth_nodes = np.asarray(l)
    
    return(cloth_nodes)


#-------------------------------------------------------------------------------------------------------------------------------------------------------
# clean_cloth
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def clean_cloth(dtm_points):
    
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function takes a Digital Terrain Model (DTM) and denoises it. This denoising is done via a 2 MADs
    from the median height value of a neighbourhood of size 15.
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------

    dtm_points: numpy array. Matrix containing (x, y, z) coordinates of the DTM points.
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    clean_points: numpy array. Matrix containing (x, y, z) coordinates of the denoised DTM points.
    '''
    
    from scipy.spatial import cKDTree
    tree = cKDTree(dtm_points[:,:2])
    d, indexes = tree.query(dtm_points[:, :2], 15)
    abs_devs = np.abs(dtm_points[:,2] - np.median(dtm_points[:, 2][indexes], axis = 1))
    mads = np.median(abs_devs)
    clean_points = dtm_points[abs_devs < 2 * mads]
    return clean_points 

#-------------------------------------------------------------------------------------------------------------------------------------------------------
# normalize_heights
#-------------------------------------------------------------------------------------------------------------------------------------------------------

def normalize_heights(cloud, dtm_points):
    '''
    -----------------------------------------------------------------------------
    ------------------           General description           ------------------
    -----------------------------------------------------------------------------

    This function takes a point cloud and a Digital Terrain Model (DTM) and normalizes the heights
    of the first based on the second.
    -----------------------------------------------------------------------------
    ------------------                 Inputs                  ------------------
    -----------------------------------------------------------------------------
    
    cloud: numpy array. Matrix containing (x, y, z) coordinates of the point cloud.
    dtm_points: numpy array. Matrix containing (x, y, z) coordinates of the DTM points.
    
    -----------------------------------------------------------------------------
    -----------------                 Outputs                  ------------------
    -----------------------------------------------------------------------------

    zs_diff_triples: numpy array. Vector containing the normalized height values for the points in 'cloud'.
    '''
    from scipy.spatial import cKDTree
    tree = cKDTree(dtm_points[:,:2])
    d, idx_pt_mesh = tree.query(cloud[:,:2], 3)
    # Z point cloud - Z dtm (Weighted average, based on distance)
    zs_diff_triples = cloud[:,2] - np.average(dtm_points[:, 2][idx_pt_mesh],weights = d, axis = 1)
    return zs_diff_triples #vector containing the normalized heights for the points in point_cloud_xyz
