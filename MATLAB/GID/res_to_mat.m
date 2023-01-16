clearvars
fname = 'wall_numge_uniform_ascii_34sec';

if ~exist('mesh_data.mat')

fid = fopen([fname '.msh']);
step = 1;
while ~feof(fid)
l = fgetl(fid);
if contains(l,'Group')
disp(['Extracting mesh data at step: ' num2str(step)])
    
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
while ~contains(l,'end coordinates')
node = str2double((split(l)))';
mat_nodes(node(1),:)=node(2:4);
l = fgetl(fid);
end
while ~contains(l,'MESH "Kratos_Triangle2D3_Mesh_1" dimension 3 ElemType Triangle Nnode 3')
l = fgetl(fid);
end
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
while ~contains(l,'end elements')
element = str2double((split(l)))';
mat_elements(element(1),:)=element(2:end);    
l = fgetl(fid);
end
myMesh(step).Elements = mat_elements;
myMesh(step).Nodes = mat_nodes;
mat_nodes = [];
mat_elements = [];
step = step+1;
end
fgetl(fid);
end
fclose(fid);
save('mesh_data.mat','myMesh');
else
    load mesh_data.mat
end
%% 
if ~exist('results.mat')
fid = fopen([fname '.res']);
step = 1;
old_time = 0.0;
while ~feof(fid)
while ~contains(l,'"Kratos" ')
    l = fgetl(fid);
end
fgetl(fid);
fgetl(fid);
l = strsplit(l);
result_name = l{2};
result_name = split(result_name,'//');
result_name = strrep(result_name{1},'"','');
time = str2double(l{4});
disp(['Extracting results data at step: ' num2str(step) ', time: ' num2str(time) ', for variable: ' result_name])

if time~=old_time
old_time = time;
step = step+1;
end

l = fgetl(fid);

mat_values = [];
while ~contains(l,"End values")
values = str2double((split(l)))';
if isnan(values(1))
values(1)=[];
end
mat_values(values(1),:)=values(2:end);
l = fgetl(fid);
end
eval(['myResults(' num2str(step) ').' result_name '=mat_values;']);
myResults(step).Time = time;
l = fgetl(fid);
end
save('results.mat','myResults');
else
load results;
end