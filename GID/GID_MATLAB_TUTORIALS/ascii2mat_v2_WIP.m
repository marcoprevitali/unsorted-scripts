clearvars
folders = dir('*_pedone_SNW_drained_putty_ascii');

    fidx=1;
fname = folders(fidx).name;

cd(fname);

fname2 = strrep(fname,'.gid','_ascii');

fid = fopen([fname2 '.msh']);
step = 1;
l = fgetl(fid);
while ~feof(fid)
if contains(l,'ElemType Point Nnode')
disp(['Extracting node data at step: ' num2str(step)])
    
%l = fgetl(fid);
%l = fgetl(fid);
l = fgetl(fid);
l = fgetl(fid);
nnodes = 1;
while ~contains(l,'end coordinates')
node = str2double((split(l)))';
mat_nodes(nnodes,:)=node;
l = fgetl(fid);

nnodes = nnodes+1;
end

myMesh(step).Nodes = mat_nodes;
mat_nodes = [];
while ~contains(l,'end group')
while and(~contains(l,'dimension 3 ElemType Triangle Nnode 3'),~contains(l,'end group'))
l = fgetl(fid);
if l==-1 break; end
end
if ~contains(l,'end group')
tmp = strfind(l,'"');
mesh_name = l(tmp(1)+1:tmp(2)-1);

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
disp(['Doing mesh: ' mesh_name]);
eval(['myMesh(step).' mesh_name ' = mat_elements;']);

mat_elements = [];


end
l=fgetl(fid);


end
step = step+1;
disp('---------------')
end
l = fgetl(fid);

end
fclose(fid);



%% 
fid = fopen([fname2 '.res']);
step = 1;
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
fclose('all');
cd ..
save([fname2 '_mesh_data.mat'],'myMesh');
save([fname2 '_results.mat'],'myResults','-v7.3')


