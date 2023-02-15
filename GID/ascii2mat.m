clearvars
fname = 'wall_qs_v2_ascii';

if ~exist([fname '_mesh_data.mat'])

fid = fopen([fname '.msh']);
step = 1;
l = fgetl(fid);
while ~feof(fid)
if contains(l,'ElemType Point Nnode')
disp(['Extracting mesh data at step: ' num2str(step)])
    
%l = fgetl(fid);
%l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
nnodes = 1;
while ~contains(l,'end coordinates')
node = str2double((split(l)))';
mat_nodes(nnodes,:)=node(2:4);
l = fgetl(fid);
nnodes = nnodes+1;
end
while ~contains(l,'MESH "Kratos_Triangle2D3_Mesh_1" dimension 3 ElemType Triangle Nnode 3')
l = fgetl(fid);
if l==-1 break; end
end
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
if l==-1 break; end
nelements = 1;
while ~contains(l,'end elements')
element = str2double((split(l)))';
mat_elements(nelements,:)=element;    
l = fgetl(fid);
nelements = nelements+1;
if l==-1 break; end
end
%mat_nodes(mat_nodes(:,1)==0,:)=[];
%mat_elements(mat_elements(:,1)==0,:)=[];
myMesh(step).Elements = mat_elements;
myMesh(step).Nodes = mat_nodes;
mat_nodes = [];
mat_elements = [];
step = step+1;
end
l=fgetl(fid);
end
fclose(fid);
save([fname '_mesh_data.mat'],'myMesh');
else
    load([fname '_mesh_data.mat']);
end
%% 
if ~exist([fname '_results.mat'])
fid = fopen([fname '.res']);
step = 0;
old_time = 0.0;
l = fgetl(fid);
while ~feof(fid)
while ~contains(l,'"Kratos" ')
    l = fgetl(fid);
    if l==-1 break; end
end
fgetl(fid);
fgetl(fid);
if l==-1 break; end
l = strsplit(l);
result_name = l{2};
result_name = split(result_name,'//');
result_name = strrep(result_name{1},'"','');
time = str2double(l{4});

if time~=old_time
old_time = time;
step = step+1;
end

l = fgetl(fid);

mat_values = [];
nvalues = 1;
while ~contains(l,"End values")
values = str2double((split(l)))';
if isnan(values(1))
values(1)=[];
end
mat_values(nvalues,:)=values;
l = fgetl(fid);
nvalues=nvalues+1;
end
try
eval(['tmp = myResults(' num2str(step) ').' result_name ';']);
if numel(tmp)<numel(mat_values)
eval(['myResults(' num2str(step) ').' result_name '=mat_values;']);
disp(['Overwriting results data at step: ' num2str(step) ', time: ' num2str(time) ', for variable: ' result_name])
end
catch
eval(['myResults(' num2str(step) ').' result_name '=mat_values;']);
disp(['Extracting results data at step: ' num2str(step) ', time: ' num2str(time) ', for variable: ' result_name])
end
myResults(step).Time = time;
l = fgetl(fid);
end
save([fname '_results.mat'],'myResults','-v7.3')
else
    load([fname '_results.mat']);
end