close all
numDrop4Loss = 20;
frameRate = 1000;
boulder_mass = 0.544;
video_bool = true;
if video_bool
outputVideo = VideoWriter(['test1_out.mp4' ],'MPEG-4');
outputVideo.FrameRate = 30;
open(outputVideo)
end
%% if the region of interest, the pixel2m etc.. is not defined, it will try to define it here

files = dir('Frames/*.tiff');
I = imread([files(1).folder '/' files(1).name]);

if ~exist('x1')
imshow(I)
title('Pick the ROI extents')
[x1,y1]=ginput(1);
hold on
plot(x1,y1,'ro');
[x2,y2]=ginput(1);
plot(x1,y1,'ro');
title('Pick 2 points 5 cm distant on the ruler');
[x3,y3]=ginput(1);
plot(x3,y3,'g.');
[x4,y4]=ginput(1);
plot(x4,y4,'g.');
minX = min([x1 x2]);
maxX = max([x1 x2]);
minY = min([y1 y2]);
maxY = max([y1 y2]);
pixel2m = 0.05/((x3-x4)^2+(y3-y4)^2)^0.5;


% velocity? dunno
clf
I = imread([files(3).folder '/' files(3).name]);
imshow(I);
[x5,y5]=ginput(1);
I = imread([files(4).folder '/' files(4).name]);
imshow(I);
[x6,y6]=ginput(1);
end

impact_vel = abs(y5-y6)*pixel2m*frameRate;
drop_height = impact_vel^2*0.5/9.81;



if ~exist('parameters_threshold')
colorThresholder;
parameters_threshold=':^)';

error('Copy the mask parameters you wankpuffin')
end

minBlobArea = 50; %min fragment size in pixel

% this is just a structure from the computer vision toolbox. search
% blobanalysis
blobAnalyser = vision.BlobAnalysis( 'AreaOutputPort',true, ...
    'CentroidOutputPort', true,  'BoundingBoxOutputPort', true, ...
    'MinimumBlobArea', minBlobArea, 'ExcludeBorderBlobs',true,'MaximumCount',1000);

% create a number of tracks (i.e. number of fragments in a given frame),
% it's just something to carry out kalman filtering + computer vision just
% google it
tracks = struct(...
    'id',           {}, ...      
    'bbox',         {}, ...       
    'kalmanFilter', {}, ...     
    'age',               {}, ...  
    'totalVisibleCount', {}, ...      
    'consecutiveInvisibleCount', {});
nextId = 1; 
numTracks = 1000;
numVideoFrames = length(files);
centroidLog = nan(numTracks,2*numVideoFrames);
eccentricityLogs = nan(numTracks,numVideoFrames);
areasLogs = nan(numTracks,numVideoFrames);
orientationLogs = nan(numTracks,numVideoFrames);
frameCount = 1;
%%
clf
ref_I = I;
for fidx = 1:length(files)
im2 = imread([files(fidx).folder '/' files(fidx).name]);
im = im2-ref_I;
warning off
I = im(minY:maxY,minX:maxX,:); %clip the original image to the ROI
warning on
BW = createMask(I);
BW = bwareaopen(BW,10); %remove small particles (i.e. reflections? can comment this out if you have tiny particles)

% split the image with watershed. this doesn't do anything rn
%L = splitWS(I);
% this part is just if you want to output a movie
if video_bool
clf
imshow(im2);
hold on

plot([minX minX maxX maxX minX],[minY maxY maxY minY minY],'g--')

[B,L] = bwboundaries(BW);
for k = 1:length(B)
   boundary = B{k};
   plot(minX+boundary(:,2), minY+boundary(:,1), 'r', 'LineWidth', 1)
end
drawnow
frame = getframe(gcf);
frame = frame2im(frame);
writeVideo(outputVideo,frame)
end


% the blob analyzer does its kalman filtering and extracts stuff. the area
% is not used for tracking but it can be useful???
[areas,centroids, bboxes] = step(blobAnalyser, BW);
    
rp = regionprops(BW,'all');
rp([rp.Area]<minBlobArea)=[];
centroids2 = reshape([rp.Centroid],2,size(rp,1))';
%areas = [rp.Area]';

% try to extract the position and predict the next position of the markers
% using a kalman filter
    for i = 1:length(tracks)
        bbox = tracks(i).bbox;    
        predictedPosition = int32(predict(tracks(i).kalmanFilter));
        tracks(i).bbox = [predictedPosition - bbox(3:4)/2, bbox(3:4)];
        
    end
    
% stuff to assign a new position of the blob in the track. it depends on
% the cost of assignment (i.e. how far away it is from the expected
% position) and the cost of non-assignment (i.e. how much we want to track
% the position at a given frame).
    cost = zeros(length(tracks), size(centroids, 1));       
    for i = 1:length(tracks)
        cost(i, :) = distance(tracks(i).kalmanFilter, centroids);
    end
    
     costOfNonAssignment = 20;   
    [assignments, unassignedTracks, unassignedDetections] = ...
        assignDetectionsToTracks(cost, costOfNonAssignment);
    
    % more stuff based on the degree of confidence, etc.. 
    for i = 1:size(assignments, 1)
        trackIdx = assignments(i, 1);          
        detectionIdx = assignments(i, 2);      
        centroid = centroids(detectionIdx, :);  
        bbox = bboxes(detectionIdx, :);         
        correct(tracks(trackIdx).kalmanFilter, centroid);
        
        tracks(trackIdx).bbox = bbox;
        tracks(trackIdx).age = tracks(trackIdx).age + 1;
        tracks(trackIdx).totalVisibleCount = ...
            tracks(trackIdx).totalVisibleCount + 1;
        tracks(trackIdx).consecutiveInvisibleCount = 0;
    end
    
    %   stuff to consider that something has been gone for a few frames ->
    %   probably gone4ever?
    for i = 1:length(unassignedTracks)
        ind = unassignedTracks(i);
        tracks(ind).age = tracks(ind).age + 1;
        tracks(ind).consecutiveInvisibleCount = ...
            tracks(ind).consecutiveInvisibleCount + 1;
    end

    if ~isempty(tracks)
        % compute the fraction of the track's age for which it was visible
        ages = [tracks(:).age];
        totalVisibleCounts = [tracks(:).totalVisibleCount];
        visibility = totalVisibleCounts ./ ages;     
        % find the indices of 'lost' tracks
        lostInds = (ages < 4 & visibility < 0.6) | ...
            ([tracks(:).consecutiveInvisibleCount] >= numDrop4Loss);  
        tracks = tracks(~lostInds); 
    end
    

    centroids1 = centroids(unassignedDetections, :);           % Nx2 double
    bboxes = bboxes(unassignedDetections, :);                 % Nx4 int32
    
    % the same thing again after removing the missing detections
    for i = 1:size(centroids1, 1)
        
        centroid = centroids1(i,:);
        bbox = bboxes(i, :);
        
      kalmanFilter = configureKalmanFilter('ConstantVelocity', ...
            centroid, [200, 50], [100, 25], 100);
        
        newTrack = struct(...
            'id', nextId, ...
            'bbox', bbox, ...
            'kalmanFilter', kalmanFilter, ...
            'age', 1, ...
            'totalVisibleCount', 1, ...
            'consecutiveInvisibleCount', 0);
        
        tracks(end + 1) = newTrack;
        
        nextId = nextId + 1;
    end
    
    
    frame = im2uint8(im);
    % putting both reliable and non-reliable tracks together
    if ~isempty(tracks)
        
        reliableTrackInds = ...
            [tracks(:).totalVisibleCount] > 0;
        reliableTracks = tracks(reliableTrackInds);
        
        if ~isempty(reliableTracks)
            bboxes = cat(1, reliableTracks.bbox);
            
            ids = int32([reliableTracks(:).id]);
            

            labels = cellstr(int2str(ids'));
            predictedTrackInds = ...
                [reliableTracks(:).consecutiveInvisibleCount] > 0;
            isPredicted = cell(size(labels));
            isPredicted(predictedTrackInds) = {' predicted'};
            labels = strcat(labels, isPredicted);
            % pretty plots
            frame = insertObjectAnnotation(frame, 'rectangle', ...
                bboxes, labels);
       %     imshow(frame)
            disp(['Step number: ' num2str(fidx) '/' num2str(length(files)) ', tracking ' num2str(length(ids)) ' object.']);

        end



    end

try
    
    ids = int32([tracks(:).id]);
    bboxTracked = cat(1,tracks.bbox);
    centroidLog(ids,(frameCount-1)*2+1:(frameCount-1)*2+2) = bboxTracked(:,1:2);


    centroids = bboxTracked(:,1:2);
    eccentricities = nan(size(centroids,1),1);
    orientations = nan(size(centroids,1),1);
    areas_empty = nan(size(centroids,1),1);
    if length(areas)==size(centroids,1)
    
        for i = 1:size(centroids2,1)
            ii = find(areas(i)==[rp.Area],1);
            orientations(ii)=rp(i).Orientation;
            eccentricities(ii)=rp(i).Eccentricity;
            areas_empty(ii)=areas(i);
            
        end
        disp('All blob centroids have been tracked from the previous steps')
    else
    for i = 1:size(centroids2,1)
       a = centroids2(i,:);
       d = [];
        for j = 1:size(centroids,1)
            b = double(centroids(j,:));
            d(j) = sum((a-b).^2)^0.5;
        end
        if min(d)<5
            ii = find(d==min(d),1);
            orientations(ii)=rp(i).Orientation;
            eccentricities(ii)=rp(i).Eccentricity;
            areas_empty(ii)=rp(i).Area;
        end
    end
        disp(['A total of ' num2str(size(centroids2,1)-length(areas)) '/' num2str(size(centroids2,1)) ' blob centroids have been calculated by Susan Calman'])
    end
    

  %  areas(ii)=rp(i).Area;
        
    



    areasLogs(ids,frameCount) = areas_empty';
    orientationLogs(ids,frameCount)=orientations';
    eccentricityLogs(ids,frameCount)=eccentricities';
    disp(['A total of ' num2str(length(areas_empty)) ' valid tracks is identified for frame: ' num2str(frameCount) '/' num2str(numVideoFrames)])

    catch
    disp(['No valid tracks found for frame: ' num2str(frameCount) '/' num2str(numVideoFrames)])
    end
     frameCount = frameCount + 1;
     disp('----------------------')
end
if video_bool
close(outputVideo)
end
% since the centroidLog is XYXYXYXYXYXY i skip 1 for each particle
centroidLog(centroidLog==0)=nan;
x = centroidLog(:,1:2:end)';
y = centroidLog(:,2:2:end)';
mat_area = double(areasLogs');
mat_area(mat_area==0)=nan;
mat_area = mat_area * pixel2m^2;
my_or = orientationLogs';
my_ecc = eccentricityLogs';
for i = 1:1000
mat_vel(:,i) = ((diff(x(:,i)*pixel2m).^2+diff(y(:,i)*pixel2m).^2).^0.5)*frameRate;
mat_spin(:,i) = diff(my_or(:,i))*frameRate;
end
%%
figure
% plot the results
subplot(1,2,1)
plot(x*pixel2m,y*pixel2m,'.')
xlabel('X [m]'); ylabel('Y [m]');
subplot(1,2,2)
yyaxis left
plot([1:size(x,1)]'/frameRate,x*pixel2m)
ylabel('X [m]')
yyaxis right
plot([1:size(x,1)]'/frameRate,y*pixel2m)
xlabel('Time [s]')
ylabel('Y [m]')
saveas(gcf,'test3_results.jpg')
figure
plot([1:length(mat_area)]'/frameRate,mat_area,'-o')
xlabel('Time [s]')
ylabel('Area [px]')
saveas(gcf,'test3_areas.jpg')

vec_mvel = max(mat_vel,[],1);
vec_marea = max(mat_area,[],1);
semilogx(vec_marea,vec_mvel,'.');
xlabel('Area [m^2]');
ylabel('Peak velocity [m/s]');
saveas(gcf,'test3_area_vel.jpg')

vec_mspin = max(mat_spin/360,[],1);
semilogx(vec_marea,vec_mspin,'.');
xlabel('Area [m^2]');
ylabel('Frequency [Hz]');
saveas(gcf,'test3_area_spin.jpg')

vec_mecc = max(my_ecc,[],1);
semilogx(vec_marea,vec_mecc,'.');
xlabel('Area [m^2]');
ylabel('Eccentricity [-]');
saveas(gcf,'test3_area_eccentricity.jpg')

function [BW,maskedRGBImage] = createMask(RGB)
%createMask  Threshold RGB image using auto-generated code from colorThresholder app.
%  [BW,MASKEDRGBIMAGE] = createMask(RGB) thresholds image RGB using
%  auto-generated code from the colorThresholder app. The colorspace and
%  range for each channel of the colorspace were set within the app. The
%  segmentation mask is returned in BW, and a composite of the mask and
%  original RGB images is returned in maskedRGBImage.

% Auto-generated by colorThresholder app on 23-Mar-2022
%------------------------------------------------------

% Convert RGB image to chosen color space
I = rgb2hsv(RGB);

% Define thresholds for channel 1 based on histogram settings
channel1Min = 0.078;
channel1Max = 0.013;

% Define thresholds for channel 2 based on histogram settings
channel2Min = 0.000;
channel2Max = 1.000;

% Define thresholds for channel 3 based on histogram settings
channel3Min = 0.1;
channel3Max = 1.000;

% Create mask based on chosen histogram thresholds
sliderBW = ( (I(:,:,1) >= channel1Min) | (I(:,:,1) <= channel1Max) ) & ...
    (I(:,:,2) >= channel2Min ) & (I(:,:,2) <= channel2Max) & ...
    (I(:,:,3) >= channel3Min ) & (I(:,:,3) <= channel3Max);
BW = sliderBW;

% Initialize output masked image based on input image.
maskedRGBImage = RGB;

% Set background pixels where BW is false to zero.
maskedRGBImage(repmat(~BW,[1 1 3])) = 0;
end

function L = splitWS(I)
I = rgb2gray(I);
%%
gmag = imgradient(I);
imshow(gmag,[])
title('Gradient Magnitude')

L = watershed(gmag);
Lrgb = label2rgb(L);
imshow(Lrgb)
title('Watershed Transform of Gradient Magnitude')
se = strel('disk',20);
Io = imopen(I,se);
imshow(Io)
title('Opening')
% Next compute the opening-by-reconstruction using |imerode| and |imreconstruct|.

Ie = imerode(I,se);
Iobr = imreconstruct(Ie,I);
imshow(Iobr)
title('Opening-by-Reconstruction')
% Following the opening with a closing can remove the dark spots and stem marks. 
% Compare a regular morphological closing with a closing-by-reconstruction. First 
% try |imclose|:

Ioc = imclose(Io,se);
imshow(Ioc)
title('Opening-Closing')
% Now use |imdilate| followed by |imreconstruct|. Notice you must complement 
% the image inputs and output of |imreconstruct|.

Iobrd = imdilate(Iobr,se);
Iobrcbr = imreconstruct(imcomplement(Iobrd),imcomplement(Iobr));
Iobrcbr = imcomplement(Iobrcbr);
imshow(Iobrcbr)
title('Opening-Closing by Reconstruction')
% As you can see by comparing |Iobrcbr| with |Ioc|, reconstruction-based opening 
% and closing are more effective than standard opening and closing at removing 
% small blemishes without affecting the overall shapes of the objects. Calculate 
% the regional maxima of |Iobrcbr| to obtain good foreground markers.

fgm = imregionalmax(Iobrcbr);
imshow(fgm)
title('Regional Maxima of Opening-Closing by Reconstruction')


I2 = labeloverlay(I,fgm);
imshow(I2)
title('Regional Maxima Superimposed on Original Image')
 
se2 = strel(ones(5,5));
fgm2 = imclose(fgm,se2);
fgm3 = imerode(fgm2,se2);

fgm4 = bwareaopen(fgm3,5);
I3 = labeloverlay(I,fgm4);
imshow(I3)
title('Modified Regional Maxima Superimposed on Original Image')

bw = imbinarize(Iobrcbr);
imshow(bw)
title('Thresholded Opening-Closing by Reconstruction')

D = bwdist(mat2gray(-bw));
DL = watershed(D);
bgm = DL == 0;
imshow(bgm)
title('Watershed Ridge Lines')


gmag2 = imimposemin(gmag, bgm | fgm4);


L = watershed(gmag2);


labels = imdilate(L==0,ones(3,3)) + 2*bgm + 3*fgm4;
I4 = labeloverlay(I,labels);
imshow(I4)
title('Markers and Object Boundaries Superimposed on Original Image')


Lrgb = label2rgb(L,'jet','w','shuffle');
imshow(Lrgb)
title('Colored Watershed Label Matrix')

imshow(I)
hold on
himage = imshow(Lrgb);
himage.AlphaData = 0.3;
title('Colored Labels Superimposed Transparently on Original Image')

end