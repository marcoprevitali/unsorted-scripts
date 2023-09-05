clearvars

files = dir('*msh');

for fidx = 1:length(files)
    
fname = files(fidx).name;

line_in_text = 1;

fname2 =strrep(fname,'.msh','');
%%
fid = fopen(fname);
step = 1;
l = fgetl(fid);
line_in_text = line_in_text+1;
while ~feof(fid)
while contains(l,'ElemType Tetrahedra Nnode')
disp(['Extracting node data at step: ' num2str(step)])
tmp = strfind(l,'"');
meshName = l(tmp(1)+1:tmp(2)-1);
%l = fgetl(fid);
%l = fgetl(fid);
l = fgetl(fid);
line_in_text = line_in_text+1;
l = fgetl(fid);
line_in_text = line_in_text+1;
nnodes = 1;
mat_nodes = [];
while ~contains(l,'end coordinates')
node = str2double((split(l)))';
mat_nodes(nnodes,:)=node;
l = fgetl(fid);
line_in_text = line_in_text+1;
nnodes = nnodes+1;
end

if ~isempty(mat_nodes)
myMesh(step).Nodes = mat_nodes;
end
l = fgetl(fid);
l = fgetl(fid);
line_in_text = line_in_text+1;
line_in_text = line_in_text+1;

nelements = 1;
l = fgetl(fid);
line_in_text = line_in_text+1;
while ~contains(l,'end elements') 
if l==-1 
    break;
end




element = str2double((split(l)))';
element(isnan(element))=[];
element(end) = [];
mat_elements(nelements,1:5)=element;    

l = fgetl(fid);
line_in_text = line_in_text+1;
nelements = nelements+1;
end
%mat_nodes(mat_nodes(:,1)==0,:)=[];
%mat_elements(mat_elements(:,1)==0,:)=[];
eval(['myMesh(step).' meshName '= mat_elements;']);
disp(['Extracted mesh ' meshName ' at step: ' num2str(step)])

mat_elements = [];
nelements = 1;


mat_nodes = [];
l = fgetl(fid);
line_in_text = line_in_text+1;

end

l=fgetl(fid);
line_in_text = line_in_text+1;

if contains(l,'end group')
step = step+1;
end


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

if time~=old_time && ~isnan(time)
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
save([fname2 '_mesh_data.mat'],'myMesh');
save([fname2 '_results.mat'],'myResults','-v7.3')
%     catch
%         disp('Couldnt get the data :(');
end

