clear all
clc

%% Front Crater Volume
% Volume from Z slices

cd 'D:/LAB_JHU/Experimental_Data/HyFire/Shot4_test/shot15';

IZFstart = 785; % I: images, Z: Z slices, F: Front face
IZFend = 787;
prefix = 'slice';
ZFimages = {};
ZFimagesBW = {};
VX = 43.6353;    % Voxel size in X direction in microns
VY = 43.6353;    % Voxel size in Y direction in microns
VZ = 43.6353;    % Voxel size in Z direction in microns

% Read images
for i = IZFstart:IZFend
   str = num2str(i,'%05.f');
   im_name = strcat(prefix,str,'.tif');
   ZFimages{i} = im2double(imread(im_name));
   T = adaptthresh(ZFimages{i},0.6,'ForegroundPolarity','bright');    
   ZFimagesBW{i} = imbinarize(ZFimages{i}, 0.4);    % Binarize Images
   imshowpair(ZFimages{i},ZFimagesBW{i},'montage');
end

% Find the rectangular region of interest
imshow(ZFimages{IZFstart+1});
title('Select region for displacement calculation.');
ROI = getrect;
close;
%
IBW = {};

% Find black pixels in the ROI in an image. Find volume of crater.
volZF = 0;   % volume of crater in um^3.
for i = IZFstart:IZFend
   I =  ZFimages{i};
   I = I(ROI(2):ROI(2) + ROI(4), ROI(1):ROI(1) + ROI(3));
    
   IBW{i} =  ZFimagesBW{i};
   IBW{i} = IBW{i}(ROI(2):ROI(2) + ROI(4), ROI(1):ROI(1) + ROI(3));
   [row, col, v] = find(~IBW{i});     % Find all zero elements
   
%   imshowpair(I,IBW{i},'montage');
%   pause(1)
%   close;
   
   numPixels = length(row);     % Number of zero elements
   A(i) = numPixels*(VX^2);     % Assuming VX = VY
   volZF = volZF + A(i)*VZ;
end

% Crater volume in mm^3.
volZF = volZF*(1e-9);    

% Contours of boundaries of the crater at different Z values.
x=0:VX:VX*(size(I,2)-1);
y=0:VY:VY*(size(I,1)-1);
[X,Y] = meshgrid(x,y);
Z = zeros(size(X));
X = flip(X,1);
Y = flip(Y,1);
Z = flip(Z,1);

for i = IZFstart:1:IZFend
   imageZ = (IBW{i}).*(VZ*(IZFend - i));
   Z = max(Z,imageZ);
end

% 3D contour plots
figure
contour3(X.*1e-3,Y.*1e-3,Z.*1e-3,IZFend-IZFstart+1,'Linewidth',2)
axis equal
axis([min(x).*1e-3 max(x).*1e-3 min(y).*1e-3 max(y).*1e-3])
box on
xlabel('X (mm)','FontSize',10,'FontWeight','bold')
ylabel('Y (mm)','FontSize',10,'FontWeight','bold')
zlabel('Z (mm)','FontSize',10,'FontWeight','bold')
title('BCShot4 Front','FontSize',12,'FontWeight','bold')
hcb = colorbar;
hcb.Title.String = "Z (mm)";

%% Interpolated 3D plot
xq = 0:VX/4:VX*(size(I,2)-1);
yq=0:VY/4:VY*(size(I,1)-1);
[Xq,Yq] = meshgrid(xq,yq);
Zq = griddata(X,Y,Z,Xq,Yq,'cubic');

X = flip(X,1);
Y = flip(Y,1);
Z = flip(Z,1);

figure
surf(Xq.*1e-3,Yq.*1e-3,Zq.*1e-3,'edgecolor','none') % 3D surface plot
axis equal
axis([min(xq).*1e-3 max(xq).*1e-3 min(yq).*1e-3 max(yq).*1e-3])
colormap(turbo)
hcb = colorbar;
box on
xlabel('X (mm)','FontSize',15,'FontWeight','bold')
ylabel('Y (mm)','FontSize',15,'FontWeight','bold')
zlabel('Z (mm)','FontSize',15,'FontWeight','bold')
%title('BCShot4 Front','FontSize',12,'FontWeight','bold')
view(25,10)%for different view angles

ax = gca;
ax.FontUnits = 'points';
ax.FontSize = 15;
ax.LineWidth = 1;

hcb = colorbar;
hcb.Title.String = "Z (mm)";

%sav